from flask import Blueprint, render_template, session, redirect
from pymongo import MongoClient
from bson import ObjectId
from config import MONGO_URI, DB_NAME, USER_COLLECTION
from google.oauth2.credentials import Credentials
from google_docs import ensure_notes_doc_for_patient

patients_bp = Blueprint("patients", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]
users_collection = db[USER_COLLECTION]


@patients_bp.route("/patient/<patient_id>")
def view_patient(patient_id):
    user = session.get("user")
    if not user or user.get("role") != "therapist":
        return redirect("/login")

    patient = patients_collection.find_one({
        "_id": ObjectId(patient_id),
        "doctor_emails": user["email"]
    })
    if not patient:
        return "Patient not found or unauthorized", 404

    db_user = users_collection.find_one({"email": user["email"]})
    if not db_user or "credentials" not in db_user:
        return redirect("/login")

    creds = Credentials(**db_user["credentials"])
    result = ensure_notes_doc_for_patient(creds, patient["_id"], patient["name"], patients_collection)

    patient["notes_doc_id"] = result["id"]

    return render_template("patient_detail_therapist.html", patient=patient)


@patients_bp.route("/view_patient/<patient_id>")
def view_patient_info(patient_id):
    user = session.get("user")
    if not user or user.get("role") not in ["secretary", "admin"]:
        return redirect("/login")

    patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    return render_template("patient_detail_admin_secretary.html", patient=patient)


@patients_bp.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect("/login")

    if user.get("role") != "therapist":
        return "Access denied: Only therapists can view the dashboard.", 403

    doctor_email = user["email"]
    patients = patients_collection.find({"doctor_emails": doctor_email})

    return render_template("dashboard.html", user=user, patients=patients)


@patients_bp.route("/secretary/therapists")
def secretary_therapist_list():
    user = session.get("user")
    if not user or user.get("role") != "secretary":
        return redirect("/login")

    therapists = list(users_collection.find({"role": "therapist"}))
    for therapist in therapists:
        therapist["patients"] = list(patients_collection.find({"doctor_emails": therapist["email"]}))

    return render_template("secretary_therapist_list.html", user=user, therapists=therapists)
