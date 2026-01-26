from pprint import pprint

from src.use_cases.health.check_mongo_connection import check_connection

if __name__ == '__main__':
    status = check_connection()
    pprint(status)
    if not status.get('ok'):
        raise SystemExit(1)
