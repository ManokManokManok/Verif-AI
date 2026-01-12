# Custom runserver that adds a --with-llm flag, delegating to staticfiles runserver
from django.contrib.staticfiles.management.commands.runserver import Command as StaticRunserverCommand

class Command(StaticRunserverCommand):
    help = 'Starts Django dev server. Use --with-llm to warm models before starting.'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--with-llm',
            action='store_true',
            help='Warm required LLM models before starting the server.'
        )

    def handle(self, *args, **options):
        if options.pop('with_llm', False):
            try:
                from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
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
        # Delegate to the original staticfiles runserver
        super().handle(*args, **options)
