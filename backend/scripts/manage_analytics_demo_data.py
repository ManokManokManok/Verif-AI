"""Preview, seed, or remove tagged community analytics presentation data."""

import argparse
import calendar
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from src.infrastructure.mongodb.connection import (  # noqa: E402
    _is_remote_uri,
    get_database_name,
    get_mongo_client,
)

BATCH_FIELD = 'analytics_demo_batch'
DEFAULT_BATCH_ID = 'community-rise-presentation-2026-09'
MONTHLY_COUNTS = {
    'Impersonation and Authority': [5, 5, 6, 6, 7, 7, 8, 8, 10, 12, 15, 22],
    'Banking Access & Payment': [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9],
    'Prize, Raffle & Reward': [5, 5, 5, 6, 6, 6, 7, 7, 8, 8, 9, 10],
}


def _month_window(now):
    current_index = now.year * 12 + now.month - 1
    months = []
    for offset in range(11, -1, -1):
        year, month_index = divmod(current_index - offset, 12)
        months.append((year, month_index + 1))
    return months


def _build_demo_documents(batch_id, now=None):
    current_time = now or datetime.now(timezone.utc)
    documents = []

    for month_index, (year, month) in enumerate(_month_window(current_time)):
        last_day = calendar.monthrange(year, month)[1]
        for type_index, (scam_type, monthly_counts) in enumerate(MONTHLY_COUNTS.items()):
            for check_index in range(monthly_counts[month_index]):
                day = min(3 + check_index % 22, last_day)
                created_at = datetime(year, month, day, 15, tzinfo=timezone.utc)
                documents.append({
                    'ref_id': f'{batch_id}:{year:04d}{month:02d}:{type_index:02d}:{check_index:02d}',
                    'user_id': f'{batch_id}:community-member:{check_index:02d}',
                    'scam_type': scam_type,
                    'is_scam': True,
                    'scam_score': 76 + (check_index % 24),
                    'type_confidence': 84 + (check_index % 15),
                    'created_at': created_at,
                    'user_deleted': False,
                    BATCH_FIELD: batch_id,
                })

        for check_index in range(8):
            day = min(5 + check_index, last_day)
            documents.append({
                'ref_id': f'{batch_id}:{year:04d}{month:02d}:legitimate:{check_index:02d}',
                'user_id': f'{batch_id}:community-member:{check_index:02d}',
                'scam_type': 'Not Scam',
                'is_scam': False,
                'scam_score': 5 + check_index,
                'type_confidence': 92,
                'created_at': datetime(year, month, day, 15, tzinfo=timezone.utc),
                'user_deleted': False,
                BATCH_FIELD: batch_id,
            })

    return documents


def _mongo_target_is_remote():
    uri = os.getenv('MONGODB_URI_BACKEND') or os.getenv('MONGODB_URI')
    if not uri:
        raise SystemExit('MONGODB_URI_BACKEND or MONGODB_URI is not configured.')
    return _is_remote_uri(uri)


def _get_collection(args):
    if _mongo_target_is_remote() and not args.allow_remote:
        raise SystemExit(
            'Refusing to modify a remote MongoDB target. Use a local demo database, '
            'or explicitly pass --allow-remote together with --apply after confirming the target.'
        )
    client = get_mongo_client(role='backend')
    return client[get_database_name()]['analysis_results']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seed', 'cleanup'))
    parser.add_argument('--batch-id', default=DEFAULT_BATCH_ID)
    parser.add_argument('--apply', action='store_true', help='Perform the requested database change. Without this, only preview.')
    parser.add_argument('--allow-remote', action='store_true', help='Permit writes to a remote MongoDB. Requires --apply as well.')
    args = parser.parse_args()

    is_remote = _mongo_target_is_remote()
    print(f'Target database: {get_database_name()} ({"remote" if is_remote else "local"}; URI hidden)')
    print(f'Demo batch tag: {BATCH_FIELD}={args.batch_id}')

    if args.action == 'seed':
        documents = _build_demo_documents(args.batch_id)
        if not args.apply:
            print(f'Dry run: would insert {len(documents)} synthetic community records across 12 months.')
            print('No database connection was opened and no records were changed.')
            return
        collection = _get_collection(args)
        existing_count = collection.count_documents({BATCH_FIELD: args.batch_id})
        if existing_count:
            raise SystemExit(f'Batch already contains {existing_count} records; clean it up before reseeding.')
        collection.insert_many(documents, ordered=True)
        print(f'Inserted {len(documents)} tagged synthetic records.')
        return

    if not args.apply:
        print(f'Dry run: would delete only records tagged {BATCH_FIELD}={args.batch_id}.')
        print('No database connection was opened and no records were changed.')
        return

    collection = _get_collection(args)
    result = collection.delete_many({BATCH_FIELD: args.batch_id})
    print(f'Removed {result.deleted_count} tagged synthetic records.')


if __name__ == '__main__':
    main()