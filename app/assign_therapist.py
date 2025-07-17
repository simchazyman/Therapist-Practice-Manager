from flask import Blueprint, render_template, request, redirect, session
from bson import ObjectId
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

assign_bp = Blueprint("assign", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]
users_collection = db["users"]

@assign_bp.route("/assign_therapist/<patient_id>", methods=["GET", "POST"])
def assign_therapist(patient_id):
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "secretary"]:
        return redirect("/login")
    

    is_admin = user.get("role") == "admin"
    patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
    
    if not is_admin and patient.get("doctor_emails"):
        return "This patient already has a therapist. Only admins can make changes.", 403



    if not patient:
        return "Patient not found", 404

    therapists = list(users_collection.find({"role": "therapist"}))

    if request.method == "POST":
        selected = request.form.getlist("therapist_emails")

        if not is_admin:
            current = patient.get("doctor_emails", [])
            if current:
                return "Secretary cannot change or remove assigned therapist(s)", 403
            if len(selected) > 1:
                return "Secretary can only assign one therapist", 403

        # Apply update
        patients_collection.update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": {"doctor_emails": selected}}
        )
        return redirect("/view_patient/" + patient_id)


    return render_template("assign_therapist.html",
                           patient=patient,
                           therapists=therapists,
                           is_admin=is_admin)
