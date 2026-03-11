from django.core.management.base import BaseCommand
import time
import json


def _resolve_metric(value):
    """Return a JSON-serializable metric value.

    Some model attributes are exposed as callables (e.g., llm.n_ctx).
    """
    if callable(value):
        try:
            value = value()
        except TypeError:
            return str(value)
    return value

class Command(BaseCommand):
    help = 'Downloads and loads required LLM models (multihead BERT, Gemma GGUF).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--targets',
            type=str,
            default='multihead,gemma',
            help='Comma-separated targets to warm: multihead,gemma'
        )

    def handle(self, *args, **options):
        targets = [t.strip() for t in options['targets'].split(',') if t.strip()]
        status = {}

        try:
            from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
        except Exception as e:
            self.stderr.write(f'Failed importing loaders: {e}')
            raise SystemExit(1)

        if 'multihead' in targets:
            start = time.time()
            try:
                tokenizer, model, scam_types = load_multihead_model()
                status['multihead'] = {
                    'ok': True,
                    'elapsed_s': round(time.time() - start, 2),
                    'hidden_size': getattr(model.bert.config, 'hidden_size', None),
                    'num_types': len(scam_types),
                }
            except ImportError as ie:
                status['multihead'] = {
                    'ok': False,
                    'error': str(ie),
                    'hint': 'Install heavy deps: pip install transformers torch',
                }
            except Exception as e:
                status['multihead'] = {
                    'ok': False,
                    'error': str(e),
                }

        if 'gemma' in targets:
            start = time.time()
            try:
                llm = load_gemma_model()
                ctx_value = _resolve_metric(getattr(llm, 'n_ctx', None))
                status['gemma'] = {
                    'ok': True,
                    'elapsed_s': round(time.time() - start, 2),
                    'ctx': ctx_value,
                }
            except ImportError as ie:
                status['gemma'] = {
                    'ok': False,
                    'error': str(ie),
                    'hint': 'Install: pip install llama-cpp-python',
                }
            except Exception as e:
                status['gemma'] = {
                    'ok': False,
                    'error': str(e),
                }

        self.stdout.write(json.dumps(status, indent=2))
        if not all(v.get('ok') for v in status.values()):
            raise SystemExit(1)
