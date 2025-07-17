from flask import Blueprint, render_template, request, redirect, session
from bson import ObjectId
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

therapist_admin_bp = Blueprint("therapist_admin", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
patients_collection = db["patients"]

@therapist_admin_bp.route("/admin/therapists")
def therapist_list():
    user = session.get("user")
    if not user or user["role"] not in ["admin", "secretary"]:
        return redirect("/login")

    therapists = list(users_collection.find({"role": "therapist"}))

    for t in therapists:
        count = patients_collection.count_documents({"doctor_emails": t["email"]})
        t["patient_count"] = count

    return render_template("therapist_list.html", user=user, therapists=therapists)


@therapist_admin_bp.route("/admin/therapist_patients/<email>")
def therapist_patients(email):
    user = session.get("user")
    if not user or user["role"] not in ["admin", "secretary"]:
        return redirect("/login")

    therapist = users_collection.find_one({"email": email})
    if not therapist:
        return "Therapist not found", 404

    patients = list(patients_collection.find({"doctor_emails": email}))

    return render_template("therapist_patients.html", user=user, therapist=therapist, patients=patients)


@therapist_admin_bp.route("/admin/unassign_patient/<patient_id>/<email>", methods=["POST"])
def unassign_patient(patient_id, email):
    user = session.get("user")
    if not user or user["role"] != "admin":
        return "Unauthorized", 403

    patients_collection.update_one(
        {"_id": ObjectId(patient_id)},
        {"$pull": {"doctor_emails": email}}
    )

    return redirect(f"/admin/therapist_patients/{email}")
