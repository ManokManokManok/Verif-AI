from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Starts Django dev server after warming required LLM models.'

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', help='Optional port/address, e.g. 127.0.0.1:8000 or 8000')

    def handle(self, *args, **options):
        try:
            from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
            # Warm both; if heavy deps missing, continue and start server
            try:
                load_multihead_model()
            except ImportError:
                self.stderr.write('Missing transformers/torch; multihead not warmed. Install heavy deps.')
            try:
                load_gemma_model()
            except ImportError:
                self.stderr.write('Missing llama-cpp-python; gemma not warmed. Install heavy deps.')
        except Exception as e:
            self.stderr.write(f'Warm-up error: {e}')
        # Start the regular dev server; default to 8000 if no addrport provided
        addrport = options.get('addrport')
        if addrport:
            call_command('runserver', addrport)
        else:
            call_command('runserver', '8000')
