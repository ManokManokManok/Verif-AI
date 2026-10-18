from django.http import JsonResponse
from src.infrastructure.ai.loaders import models_status as get_models_status
from src.infrastructure.ai.genai_provider import genai_status
from src.infrastructure.model_info import build_model_info
from src.interfaces.rest.views import detect_scam

def health(_request):
    return JsonResponse({
        'status': 'ok',
        'service': 'verfai-api',
    })


def model_info(_request):
    """Public: model accuracy / margin of error and when the dataset was last updated."""
    return JsonResponse({'success': True, 'data': build_model_info()})


def models_status(_request):
    status = {**get_models_status(), **genai_status()}
    if not status.get('multihead_loaded') or not (status.get('gemini_available') or status.get('gemma_loaded')):
        return JsonResponse({
            'ok': False,
            'message': 'The classifier or generative AI provider is not available.',
            'status': status,
        }, status=200)
    return JsonResponse({'ok': True, 'status': status})
