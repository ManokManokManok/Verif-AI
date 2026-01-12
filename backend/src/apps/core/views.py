from django.http import JsonResponse
from src.infrastructure.ai.loaders import models_status

def health(_request):
    return JsonResponse({
        'status': 'ok',
        'service': 'verfai-api',
    })


def models_status(_request):
    status = models_status()
    if not (status.get('multihead_loaded') and status.get('gemma_loaded')):
        return JsonResponse({
            'ok': False,
            'message': 'Models are not loaded. Start with `runserver --with-llm` or run `manage.py warm_models`.',
            'status': status,
        }, status=200)
    return JsonResponse({'ok': True, 'status': status})
