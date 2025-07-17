from flask import Blueprint, render_template, session, redirect
from bson import ObjectId
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

therapist_view_bp = Blueprint("therapist_view", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]

@therapist_view_bp.route("/patient/<patient_id>")
def therapist_view_patient(patient_id):
    user = session.get("user")
    if not user or user.get("role") != "therapist":
        return redirect("/login")

    patient = patients_collection.find_one({
        "_id": ObjectId(patient_id),
        "doctor_emails": user["email"]
    })

    if not patient:
        return "Patient not found or unauthorized", 404

    return render_template("patient_detail_therapist.html", patient=patient)
