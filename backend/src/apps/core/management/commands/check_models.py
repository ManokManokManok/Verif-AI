from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deprecated: model checking removed. Use warm_models to load models.'

    def handle(self, *args, **options):
        self.stdout.write('Model checking has been removed. Use: manage.py warm_models')
