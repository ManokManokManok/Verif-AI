from src.infrastructure.mongodb.connection import get_mongo_client


def check_connection() -> dict:
    """Ping MongoDB server and return a minimal status dict."""
    client = get_mongo_client()
    try:
        result = client.admin.command('ping')
        return {
            'ok': True,
            'ping': result,
        }
    except Exception as exc:
        return {
            'ok': False,
            'error': str(exc),
        }
