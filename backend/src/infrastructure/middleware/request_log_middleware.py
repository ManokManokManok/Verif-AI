"""Access log line per request, similar to Django's runserver output."""
import logging
import time

from src.infrastructure.rate_limiter import get_client_ip

logger = logging.getLogger('verfai.access')

_SKIP_PREFIXES = ('/api/health',)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)

        if request.path.startswith(_SKIP_PREFIXES):
            return response

        try:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            user_id = getattr(request, 'user_id', None) or 'anonymous'
            status = response.status_code
            line = '%s %s %s user=%s ip=%s %dms'
            args = (request.method, request.get_full_path().split('?')[0], status, user_id,
                    get_client_ip(request), elapsed_ms)
            if status >= 500:
                logger.error(line, *args)
            elif status >= 400:
                logger.warning(line, *args)
            else:
                logger.info(line, *args)
        except Exception:
            pass
        return response
