from pathlib import Path
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load env from project root
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / '.env')

_DEF_URI = os.getenv('MONGODB_URI')
_DEF_DB = os.getenv('MONGODB_DB_NAME', 'verfai')

_client = None

def get_mongo_client(uri: str | None = None) -> MongoClient:
    global _client
    if _client is None:
        uri = uri or _DEF_URI
        if not uri:
            raise RuntimeError('MONGODB_URI is not set. Add it to .env')
        _client = MongoClient(uri)
    return _client


def get_database(db_name: str | None = None):
    client = get_mongo_client()
    name = db_name or _DEF_DB
    if not name:
        raise RuntimeError('MONGODB_DB_NAME is not set. Add it to .env')
    return client[name]


def get_database_name() -> str:
    """Get database name from environment."""
    return os.getenv('MONGODB_DB_NAME', 'verfai')
