"""Create and restore compressed MongoDB backups with mongodump/mongorestore."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlsplit, urlunsplit

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_DIR = BACKEND_ROOT / "backups" / "mongodb"
BACKUP_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+_\d{8}T\d{6}Z\.archive\.gz$")
DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env", override=False)

from src.infrastructure.mongodb.connection import _enforce_tls, _is_remote_uri  # noqa: E402


def _database_name() -> str:
    database = os.getenv("MONGODB_DB_NAME", "verfai")
    if not DATABASE_NAME_PATTERN.fullmatch(database):
        raise ValueError(
            "MONGODB_DB_NAME must contain only letters, numbers, underscores, or hyphens "
            "for safe namespace-scoped restores."
        )
    return database


def _connection_uri() -> str:
    uri = os.getenv("MONGODB_URI_BACKEND") or os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("Set MONGODB_URI_BACKEND or MONGODB_URI in backend/.env.")
    require_tls = os.getenv("MONGODB_REQUIRE_TLS", "").lower() in ("1", "true", "yes")
    if _is_remote_uri(uri) or require_tls:
        uri = _enforce_tls(uri)
    return uri


def _find_tool(tool_name: str) -> str:
    executable = tool_name + (".exe" if os.name == "nt" else "")
    tools_dir = os.getenv("MONGODB_TOOLS_BIN")
    if tools_dir:
        candidate = Path(tools_dir) / executable
        if candidate.is_file():
            return str(candidate)

    located = shutil.which(executable)
    if located:
        return located

    raise FileNotFoundError(
        f"{executable} was not found. Install MongoDB Database Tools and add them to PATH, "
        "or set MONGODB_TOOLS_BIN to their bin directory."
    )


def _split_connection_uri(uri: str) -> tuple[str, Optional[str], Optional[str]]:
    parsed = urlsplit(uri)
    if parsed.scheme not in ("mongodb", "mongodb+srv"):
        raise ValueError("MongoDB connection URI must start with mongodb:// or mongodb+srv://.")

    username = None
    password = None
    hostname = parsed.netloc.rsplit("@", 1)
    if len(hostname) == 2:
        credentials, host = hostname
        username_part, separator, password_part = credentials.partition(":")
        username = unquote(username_part)
        if separator:
            password = unquote(password_part)
        sanitized_netloc = host
    else:
        sanitized_netloc = parsed.netloc

    sanitized_uri = urlunsplit(
        (parsed.scheme, sanitized_netloc, parsed.path, parsed.query, parsed.fragment)
    )
    return sanitized_uri, username, password


def _create_tool_config(password: Optional[str]) -> Optional[Path]:
    if password is None:
        return None

    config = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".yaml",
        prefix="mongodb-tools-",
        delete=False,
    )
    path = Path(config.name)
    try:
        config.write("password: " + json.dumps(password) + "\n")
    finally:
        config.close()

    if os.name != "nt":
        path.chmod(0o600)
    return path


def _run_tool(arguments: List[str], uri: str) -> None:
    safe_uri, username, password = _split_connection_uri(uri)
    config_path = _create_tool_config(password)
    try:
        command = list(arguments)
        if config_path is not None:
            command.append(f"--config={config_path}")
        if username is not None:
            command.append(f"--username={username}")
        command.append(safe_uri)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            details = (result.stderr or result.stdout or "no details reported").replace(
                uri, "[REDACTED]"
            )
            raise RuntimeError(
                f"{Path(arguments[0]).name} failed with exit code {result.returncode}: "
                f"{details.strip()[:1000]}"
            )
    finally:
        if config_path is not None:
            config_path.unlink(missing_ok=True)


def _backup_files(backup_dir: Path, database: str) -> List[Path]:
    prefix = f"{database}_"
    return sorted(
        (
            path
            for path in backup_dir.iterdir()
            if path.is_file()
            and path.name.startswith(prefix)
            and BACKUP_NAME_PATTERN.fullmatch(path.name)
        ),
        key=lambda path: path.name,
        reverse=True,
    )


def create_backup(backup_dir: Path, keep: int = 14) -> Path:
    if keep < 1:
        raise ValueError("--keep must be at least 1.")

    database = _database_name()
    uri = _connection_uri()
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = backup_dir / f"{database}_{timestamp}.archive.gz"
    partial_archive = archive.with_name(archive.name + ".partial")
    if archive.exists() or partial_archive.exists():
        raise FileExistsError(f"Backup already exists for timestamp {timestamp}.")

    try:
        _run_tool(
            [
                _find_tool("mongodump"),
                f"--db={database}",
                f"--archive={partial_archive}",
                "--gzip",
            ],
            uri,
        )
        if not partial_archive.is_file() or partial_archive.stat().st_size == 0:
            raise RuntimeError("mongodump completed without producing a non-empty archive.")
        partial_archive.replace(archive)
    finally:
        partial_archive.unlink(missing_ok=True)

    for old_backup in _backup_files(backup_dir, database)[keep:]:
        old_backup.unlink()
    return archive


def restore_backup(
    archive: Path,
    confirm_database: str,
    drop_existing: bool = False,
) -> None:
    database = _database_name()
    if confirm_database != database:
        raise ValueError(
            f"Restore cancelled: pass --confirm-database {database} to confirm the target."
        )
    if not archive.is_file():
        raise FileNotFoundError(f"Backup archive does not exist: {archive}")

    arguments = [
        _find_tool("mongorestore"),
        f"--archive={archive}",
        "--gzip",
        f"--nsInclude={database}.*",
    ]
    if drop_existing:
        arguments.append("--drop")
    _run_tool(arguments, _connection_uri())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)

    backup = commands.add_parser("backup", help="Create a compressed database archive.")
    backup.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("MONGODB_BACKUP_DIR", str(DEFAULT_BACKUP_DIR))),
        help="Backup directory (default: MONGODB_BACKUP_DIR or backend/backups/mongodb).",
    )
    backup.add_argument(
        "--keep",
        type=int,
        default=14,
        help="Number of most recent successful backups to keep (default: 14).",
    )

    restore = commands.add_parser("restore", help="Restore a compressed database archive.")
    restore.add_argument("--archive", type=Path, required=True)
    restore.add_argument(
        "--confirm-database",
        required=True,
        help="Must exactly match MONGODB_DB_NAME to confirm the restore target.",
    )
    restore.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop each target collection before restoring it; destructive.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.action == "backup":
            archive = create_backup(args.output_dir, keep=args.keep)
            print(f"Backup created: {archive}")
        else:
            restore_backup(
                args.archive,
                confirm_database=args.confirm_database,
                drop_existing=args.drop_existing,
            )
            print(f"Restore completed for database {_database_name()}.")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"MongoDB backup/restore failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
