from django.core.management.base import BaseCommand
import json

from src.use_cases.health.check_mongo_connection import check_connection


class Command(BaseCommand):
    help = 'Checks connectivity to MongoDB using configured environment values.'

    def handle(self, *args, **options):
        status = check_connection()
        self.stdout.write(json.dumps(status, indent=2))
        if not status.get('ok'):
            self.stderr.write('MongoDB connection failed.')
            # Non-zero exit code signals failure in CI/scripts
            raise SystemExit(1)
