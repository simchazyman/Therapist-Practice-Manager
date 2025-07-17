from flask import Blueprint, session, redirect, render_template, request
from pymongo import MongoClient
from bson import ObjectId
from config import MONGO_URI, DB_NAME
from edit_patient_route import create_edit_patient_route

secretary_bp = Blueprint("secretary", __name__)

# Setup MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]


create_edit_patient_route(secretary_bp)


from utils import refresh_session


@secretary_bp.route("/secretary")
def secretary_dashboard():
    user = refresh_session()
    if not user or user["role"] != "secretary":
        return redirect("/login")

    patients = list(patients_collection.find())

    # Get therapists and their assigned patients
    therapists = list(db["users"].find({"role": "therapist"}))
    for therapist in therapists:
        therapist["patients"] = list(patients_collection.find({"doctor_emails": therapist["email"]}))

    return render_template("secretary_dashboard.html", user=user, patients=patients, therapists=therapists)



@secretary_bp.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    user = refresh_session()
    if not user or user.get("role") != "secretary":
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["dob"]

        new_patient = {
            "name": name,
            "dob": dob,
            "doctor_email": None,
            "notes": []
        }

        patients_collection.insert_one(new_patient)
        return redirect("/secretary")

    return render_template("add_patient.html")

