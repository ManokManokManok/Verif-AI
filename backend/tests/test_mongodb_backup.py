import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "backup_mongodb.py"
MODULE_SPEC = importlib.util.spec_from_file_location("backup_mongodb", SCRIPT_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
backup_mongodb = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = backup_mongodb
MODULE_SPEC.loader.exec_module(backup_mongodb)


class MongoDBBackupTests(unittest.TestCase):
    def test_backup_writes_archive_atomically_and_keeps_latest_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            backup_dir = Path(directory)
            old_backups = [
                backup_dir / f"verfai_2026010{day}T000000Z.archive.gz"
                for day in range(1, 4)
            ]
            for path in old_backups:
                path.write_bytes(b"old backup")

            def fake_run(command, **kwargs):
                self.assertEqual(kwargs, {"capture_output": True, "text": True, "check": False})
                archive_path = Path(next(
                    argument.split("=", 1)[1]
                    for argument in command
                    if argument.startswith("--archive=")
                ))
                archive_path.write_bytes(b"compressed dump")
                return type("ProcessResult", (), {"returncode": 0, "stderr": "", "stdout": ""})()

            environment = {
                "MONGODB_DB_NAME": "verfai",
                "MONGODB_URI": "mongodb://backup-user:unit-test-password@localhost/verfai",
                "MONGODB_URI_BACKEND": "",
            }
            with patch.dict(os.environ, environment, clear=False), patch.object(
                backup_mongodb, "_find_tool", return_value="mongodump"
            ), patch.object(backup_mongodb.subprocess, "run", side_effect=fake_run) as run:
                archive = backup_mongodb.create_backup(backup_dir, keep=2)

            self.assertTrue(archive.is_file())
            self.assertEqual(archive.read_bytes(), b"compressed dump")
            self.assertFalse(archive.with_name(archive.name + ".partial").exists())
            self.assertEqual(len(backup_mongodb._backup_files(backup_dir, "verfai")), 2)
            command = run.call_args.args[0]
            self.assertNotIn("unit-test-password", " ".join(command))
            self.assertEqual(command[-1], "mongodb://localhost/verfai")
            self.assertIn("--username=backup-user", command)
            config_path = Path(next(
                argument.split("=", 1)[1]
                for argument in command
                if argument.startswith("--config=")
            ))
            self.assertFalse(config_path.exists())

    def test_failed_backup_removes_partial_archive_and_temporary_config(self):
        with tempfile.TemporaryDirectory() as directory:
            backup_dir = Path(directory)

            def failed_run(command, **kwargs):
                self.assertEqual(kwargs, {"capture_output": True, "text": True, "check": False})
                archive_path = Path(next(
                    argument.split("=", 1)[1]
                    for argument in command
                    if argument.startswith("--archive=")
                ))
                archive_path.write_bytes(b"partial")
                return type(
                    "ProcessResult",
                    (),
                    {"returncode": 1, "stderr": "dump failed", "stdout": ""},
                )()

            with patch.dict(
                os.environ,
                {
                    "MONGODB_DB_NAME": "verfai",
                    "MONGODB_URI": "mongodb://backup-user:unit-test-password@localhost/verfai",
                    "MONGODB_URI_BACKEND": "",
                },
                clear=False,
            ), patch.object(backup_mongodb, "_find_tool", return_value="mongodump"), patch.object(
                backup_mongodb.subprocess, "run", side_effect=failed_run
            ) as run:
                with self.assertRaisesRegex(RuntimeError, "dump failed"):
                    backup_mongodb.create_backup(backup_dir)

            self.assertEqual(list(backup_dir.iterdir()), [])
            command = run.call_args.args[0]
            config_path = Path(next(
                argument.split("=", 1)[1]
                for argument in command
                if argument.startswith("--config=")
            ))
            self.assertFalse(config_path.exists())

    def test_restore_requires_exact_database_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.archive.gz"
            archive.write_bytes(b"archive")
            with patch.dict(os.environ, {"MONGODB_DB_NAME": "verfai"}, clear=False), patch.object(
                backup_mongodb, "_find_tool"
            ), patch.object(backup_mongodb, "_run_tool") as run:
                with self.assertRaisesRegex(ValueError, "Restore cancelled"):
                    backup_mongodb.restore_backup(archive, confirm_database="other")

            run.assert_not_called()

    def test_remote_backup_connection_enforces_tls(self):
        with patch.dict(
            os.environ,
            {
                "MONGODB_URI": "mongodb://db.example.com/verfai",
                "MONGODB_URI_BACKEND": "",
                "MONGODB_REQUIRE_TLS": "false",
            },
            clear=False,
        ):
            uri = backup_mongodb._connection_uri()

        self.assertIn("tls=true", uri)
        self.assertIn("tlsAllowInvalidCertificates=false", uri)

    def test_restore_scopes_namespaces_and_requires_explicit_drop(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.archive.gz"
            archive.write_bytes(b"archive")
            with patch.dict(
                os.environ,
                {
                    "MONGODB_DB_NAME": "verfai",
                    "MONGODB_URI": "mongodb://localhost/verfai",
                    "MONGODB_URI_BACKEND": "",
                },
                clear=False,
            ), patch.object(backup_mongodb, "_find_tool", return_value="mongorestore"), patch.object(
                backup_mongodb, "_run_tool"
            ) as run:
                backup_mongodb.restore_backup(
                    archive, confirm_database="verfai", drop_existing=True
                )

            args, uri = run.call_args.args
            self.assertIn("--nsInclude=verfai.*", args)
            self.assertIn("--drop", args)
            self.assertEqual(uri, "mongodb://localhost/verfai")

    def test_tool_uses_password_config_and_sanitized_positional_uri(self):
        uri = (
            "mongodb://backup-user:unit-test%40password@db.example.com/verfai"
            "?authSource=admin"
        )
        config_paths = []

        def fake_run(command, **kwargs):
            self.assertEqual(kwargs, {"capture_output": True, "text": True, "check": False})
            config_path = Path(next(
                argument.split("=", 1)[1]
                for argument in command
                if argument.startswith("--config=")
            ))
            config_paths.append(config_path)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                'password: "unit-test@password"\n',
            )
            return type(
                "ProcessResult", (), {"returncode": 0, "stderr": "", "stdout": ""}
            )()

        with patch.object(backup_mongodb.subprocess, "run", side_effect=fake_run) as run:
            backup_mongodb._run_tool(["mongodump", "--db", "verfai"], uri)

        command = run.call_args.args[0]
        self.assertIn("--username=backup-user", command)
        self.assertEqual(command[-1], "mongodb://db.example.com/verfai?authSource=admin")
        self.assertNotIn("unit-test%40password", " ".join(command))
        self.assertEqual(len(config_paths), 1)
        self.assertFalse(config_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
