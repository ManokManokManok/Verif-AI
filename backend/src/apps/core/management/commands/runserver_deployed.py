import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key


BACKEND_DIR = Path(__file__).resolve().parents[5]
REPOSITORY_DIR = BACKEND_DIR.parent
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 8000
TUNNEL_HOST = 'http://127.0.0.1:8000'
VERCEL_ORIGIN = 'https://verif-ai-site.vercel.app'
LEGACY_VERCEL_ORIGIN = 'https://verif-ai-frontend.vercel.app'


def _powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _find_cloudflared() -> str | None:
    configured_path = os.environ.get('CLOUDFLARED_PATH')
    if configured_path:
        executable = Path(configured_path).expanduser()
        if executable.is_file():
            return str(executable)
        raise CommandError(f'CLOUDFLARED_PATH does not point to a file: {executable}')

    executable = shutil.which('cloudflared.exe') or shutil.which('cloudflared')
    if executable:
        return executable

    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        executable = Path(local_app_data) / 'Programs' / 'cloudflared' / 'cloudflared.exe'
        if executable.is_file():
            return str(executable)

    raise CommandError(
        'Could not find cloudflared. Install Cloudflare Tunnel, add it to PATH, '
        'or set CLOUDFLARED_PATH to the executable.'
    )


def _port_is_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        return connection.connect_ex((SERVER_ADDRESS, SERVER_PORT)) == 0


class Command(BaseCommand):
    help = 'Open separate PowerShell windows for Django and a temporary Cloudflare Quick Tunnel.'

    def handle(self, *args, **options):
        if os.name != 'nt':
            raise CommandError('runserver_deployed opens Windows PowerShell windows and is Windows-only.')
        if _port_is_in_use():
            raise CommandError(
                f'{SERVER_ADDRESS}:{SERVER_PORT} is already in use. Stop the existing server before starting this launcher.'
            )

        cloudflared = _find_cloudflared()
        powershell = shutil.which('powershell.exe')
        if not powershell:
            raise CommandError('Could not find powershell.exe.')

        backend_environment = os.environ.copy()
        backend_environment.update({
            'DJANGO_SECRET_KEY': get_random_secret_key(),
            'DJANGO_DEBUG': 'False',
            'DJANGO_ALLOWED_HOSTS': 'localhost,127.0.0.1,.trycloudflare.com',
            'CORS_ALLOWED_ORIGINS': f'{VERCEL_ORIGIN},{LEGACY_VERCEL_ORIGIN}',
            'FRONTEND_URL': VERCEL_ORIGIN,
            'DJANGO_TRUST_PROXY_SSL': 'True',
            'MFA_ENABLED': 'True',
            'LLM_WARMUP_ON_START': 'False',
            'PYTHONUNBUFFERED': '1',
        })

        server_script = (
            f'Set-Location -LiteralPath {_powershell_literal(str(BACKEND_DIR))}; '
            "Write-Host 'Django is available locally at http://127.0.0.1:8000'; "
            f'& {_powershell_literal(sys.executable)} manage.py runserver --noreload '
            f'{SERVER_ADDRESS}:{SERVER_PORT}'
        )
        tunnel_script = (
            "Write-Host 'Copy the new https://....trycloudflare.com URL below into both Vercel Production API variables, then redeploy.'; "
            f'& {_powershell_literal(cloudflared)} tunnel --url {_powershell_literal(TUNNEL_HOST)}'
        )

        server_process = None
        try:
            server_process = subprocess.Popen(
                [
                    powershell,
                    '-NoExit',
                    '-Command',
                    server_script,
                ],
                cwd=BACKEND_DIR,
                env=backend_environment,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            subprocess.Popen(
                [
                    powershell,
                    '-NoExit',
                    '-Command',
                    tunnel_script,
                ],
                cwd=BACKEND_DIR,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except OSError as error:
            if server_process and server_process.poll() is None:
                server_process.terminate()
            raise CommandError(f'Could not open the Django and tunnel terminals: {error}') from error

        self.stdout.write(self.style.SUCCESS(
            'Opened Django and Cloudflare Tunnel terminals. Leave both running while you use the demo. '
            'The Quick Tunnel URL changes each time; update both Vercel Production API variables and redeploy.'
        ))
