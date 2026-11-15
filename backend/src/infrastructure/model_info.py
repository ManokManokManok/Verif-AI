"""Model accuracy metadata (margin of error) and the admin-set 'dataset last updated' month."""
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SETTINGS_KEY = 'model_info'
DEFAULT_UPDATED = os.getenv('MODEL_DATASET_UPDATED_DEFAULT', '2026-07')
_MONTH_RE = re.compile(r'^(\d{4})-(0[1-9]|1[0-2])$')
MIN_YEAR, MAX_YEAR = 2020, 2100


def parse_month(value: Any) -> Optional[str]:
    """Return a normalised 'YYYY-MM' string or None when invalid."""
    if not isinstance(value, str):
        return None
    match = _MONTH_RE.match(value.strip())
    if not match or not MIN_YEAR <= int(match.group(1)) <= MAX_YEAR:
        return None
    return value.strip()


def load_accuracy_metadata() -> Dict[str, Any]:
    accuracy = float(os.getenv('MODEL_REPORTED_ACCURACY', '94.7'))
    return {
        'accuracy': round(accuracy, 1),
        # This is an approximate allowance, not a validated confidence interval.
        'margin_of_error': 4.4,
    }


def _settings_collection():
    from .mongodb.connection import get_mongo_client, get_database_name

    return get_mongo_client()[get_database_name()].app_settings


def get_dataset_updated() -> str:
    try:
        doc = _settings_collection().find_one({'_id': SETTINGS_KEY})
        stored = parse_month((doc or {}).get('dataset_updated'))
        if stored:
            return stored
    except Exception as exc:
        logger.warning('Could not read dataset_updated setting: %s', exc)
    return parse_month(DEFAULT_UPDATED) or '2026-07'


def set_dataset_updated(month: str, admin_id: Optional[str] = None) -> None:
    _settings_collection().update_one(
        {'_id': SETTINGS_KEY},
        {'$set': {
            'dataset_updated': month,
            'updated_by': admin_id,
            'updated_at': datetime.now(timezone.utc),
        }},
        upsert=True,
    )


def build_model_info() -> Dict[str, Any]:
    return {
        'dataset_updated': get_dataset_updated(),
        'accuracy': load_accuracy_metadata(),
    }
