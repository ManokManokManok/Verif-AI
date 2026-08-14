from django.apps import AppConfig
import os
import threading
import logging

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.core'

    def ready(self):
        # Optional warm-up on server start; disabled by default
        warm = os.getenv('LLM_WARMUP_ON_START', 'False').lower() in ('1', 'true', 'yes')
        if not warm:
            return
        targets = os.getenv('LLM_WARMUP_TARGETS', 'multihead,gemma')
        target_list = [t.strip() for t in targets.split(',') if t.strip()]

        def _warm():
            try:
                from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
                if 'multihead' in target_list:
                    load_multihead_model()
                if 'gemma' in target_list:
                    load_gemma_model()
                logging.getLogger(__name__).info('LLM warm-up complete: %s', ','.join(target_list))
            except Exception as e:
                logging.getLogger(__name__).warning('LLM warm-up failed: %s', e)

        threading.Thread(target=_warm, name='llm-warmup', daemon=True).start()
