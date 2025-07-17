from flask import session
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, USER_COLLECTION

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
user_collection = db[USER_COLLECTION]

def refresh_session():
    user = session.get("user")
    if not user:
        return None

    db_user = user_collection.find_one({"email": user["email"]})
    if not db_user or not db_user.get("approved", False):
        session.pop("user", None)
        return None

    session["user"] = {
        "name": db_user["name"],
        "email": db_user["email"],
        "role": db_user["role"],
        "specialization": db_user.get("specialization", "General Therapy")
    }
    return session["user"]




def credentials_to_dict(creds):
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

