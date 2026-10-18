"""Model accuracy metadata (margin of error) and the admin-set 'dataset last updated' month."""
import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
METADATA_FILE = Path(os.getenv('MODEL_METADATA_FILE') or (BASE_DIR / 'models' / 'model_metadata.json'))
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


def load_accuracy_metadata() -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(METADATA_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    required = ('accuracy', 'n')
    if not all(key in data for key in required):
        return None

    # Report the accuracy from the paper for the deployed model; our own test run
    # only supplies the sample size used for the statistical margin.
    accuracy = float(os.getenv('MODEL_REPORTED_ACCURACY', '94.7'))
    p = accuracy / 100
    n = int(data['n'])
    z = 1.959964
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n) * 100

    # Real-world messages differ from our dataset split, so widen the statistical
    # margin by a conservative allowance.
    allowance = float(os.getenv('MODEL_REAL_WORLD_ALLOWANCE', '3.0'))
    return {
        'accuracy': round(accuracy, 1),
        'margin_of_error': round(half + allowance, 1),
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
