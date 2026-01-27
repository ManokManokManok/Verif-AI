"""
Script to add a user_id field to all existing user documents in the MongoDB users collection.
The user_id will be set to the string value of the existing _id field.
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")
USERS_COLLECTION = "users"  # Change if your collection name is different


def add_user_id_to_existing_users():
    if not MONGO_URI or not DB_NAME:
        print("MONGODB_URI or MONGODB_DB_NAME not set in .env!")
        return
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users = db[USERS_COLLECTION]
    # Find users missing user_id
    for user in users.find({"user_id": {"$exists": False}}):
        user_id_str = str(user["_id"])
        users.update_one({"_id": user["_id"]}, {"$set": {"user_id": user_id_str}})
        print(f"Updated user {user_id_str} with user_id {user_id_str}")
    print("Migration complete.")

if __name__ == "__main__":
    add_user_id_to_existing_users()
