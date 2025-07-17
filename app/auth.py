from flask import Blueprint, redirect, render_template, url_for, session, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from pymongo import MongoClient
import os
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, MONGO_URI, DB_NAME, USER_COLLECTION
from utils import credentials_to_dict

auth_bp = Blueprint("auth", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
user_collection = db[USER_COLLECTION]

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=SCOPES
)



@auth_bp.route("/login")
def login():
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(prompt="select_account")
    session["state"] = state
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(credentials.id_token, requests.Request(), CLIENT_ID)

    existing_user = user_collection.find_one({"email": id_info["email"]})
    if not existing_user:
        user_collection.insert_one({
            "name": id_info["name"],
            "email": id_info["email"],
            "role": "pending",
            "specialization": "",
            "approved": False
        })
        role = "pending"
        specialization = ""
    else:
        role = existing_user.get("role", "therapist")
        specialization = existing_user.get("specialization", "General Therapy")

    session["user"] = {
        "name": id_info["name"],
        "email": id_info["email"],
        "role": role,
        "specialization": specialization
    }

    session["credentials"] = credentials_to_dict(credentials)
    user_collection.update_one(
        {"email": id_info["email"]},
        {"$set": {"credentials": credentials_to_dict(credentials)}}
    )

    if role == "pending":
        return redirect("/waiting_for_approval")

    if role == "therapist":
        return redirect("/dashboard")
    elif role == "admin":
        return redirect("/admin")
    elif role == "secretary":
        return redirect("/secretary")
    else:
        return "Access denied: Unknown role", 403




@auth_bp.route("/waiting_for_approval")
def waiting_for_approval():
    return render_template("waiting_for_approval.html")
