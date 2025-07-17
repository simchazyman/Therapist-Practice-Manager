from flask import Blueprint, render_template, request, session, redirect
from bson import ObjectId
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, USER_COLLECTION
from google_docs import ensure_notes_doc_for_patient

calendar_bp = Blueprint("calendar", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]
users_collection = db[USER_COLLECTION]

from bson import ObjectId  # Ensure this is at the top of your file

@calendar_bp.route("/schedule_session", methods=["GET", "POST"])
def schedule_session():
    user = session.get("user")
    if not user or user.get("role") not in ["therapist", "secretary", "admin"]:
        return redirect("/login")

    if request.method == "POST":
        # Convert patient_id to ObjectId safely
        patient_id_str = request.form["patient_id"]
        try:
            patient_id = ObjectId(patient_id_str)
        except:
            return "Invalid patient ID", 400

        session_date = request.form["session_date"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        description = request.form["description"]

        start_datetime = f"{session_date}T{start_time}:00"
        end_datetime = f"{session_date}T{end_time}:00"

        # Fetch patient record
        patient = patients_collection.find_one({"_id": patient_id})
        if not patient:
            return "Patient not found", 404

        patient_name = patient["name"]

        # Find assigned therapist
        assigned_emails = patient.get("doctor_emails", [])
        if not assigned_emails:
            return "No therapist assigned to this patient", 400

        if user["role"] == "therapist":
            therapist_email = user["email"]
            if therapist_email not in assigned_emails:
                return "You are not assigned to this patient", 403
        else:
            therapist_email = request.form.get("therapist_email")
            if therapist_email not in assigned_emails:
                return "Selected therapist is not assigned to this patient", 400

        therapist = users_collection.find_one({"email": therapist_email})
        if not therapist or "credentials" not in therapist:
            return f"Therapist {therapist_email} has not authorized Google access", 400

        # Use therapist's credentials
        creds = Credentials(**therapist["credentials"])
        calendar_service = build("calendar", "v3", credentials=creds)

        # Create calendar event
        event = {
            "summary": f"Session with {patient_name}",
            "description": f"{description}\n\nPatient: {patient_name}",

            "start": {"dateTime": start_datetime, "timeZone": "America/New_York"},
            "end": {"dateTime": end_datetime, "timeZone": "America/New_York"}
        }

        created_event = calendar_service.events().insert(calendarId="primary", body=event).execute()

        # Create/retrieve session doc
        notes_doc = ensure_notes_doc_for_patient(creds, patient_id, patient_name, patients_collection)

        # Save note with therapist info
        patients_collection.update_one(
            {"_id": patient_id},
            {
                "$push": {
                    "notes": {
                        "date": session_date,
                        "text": description,
                        "calendar_event_id": created_event["id"],
                        "calendar_event_link": created_event["htmlLink"],
                        "notes_doc_link": notes_doc["url"],
                        "therapist_email": therapist_email
                    }
                }
            }
        )

        # Redirect to correct patient view after scheduling
        if user["role"] == "therapist":
            return redirect(f"/patient/{patient_id}")
        else:
            return redirect(f"/view_patient/{patient_id}")

    # GET request
    if user["role"] == "therapist":
        patient_list = list(patients_collection.find({"doctor_emails": user["email"]}))
        therapist_email = user["email"]
    else:
        patient_list = list(patients_collection.find())
        therapist_email = None  # will be chosen in form

    patient_id = request.args.get("patient_id", "")
    patient_name = ""

    # Try to resolve name from patient_id
    if patient_id:
        try:
            pid = ObjectId(patient_id)
            patient = patients_collection.find_one({"_id": pid})
            if patient:
                patient_name = patient.get("name", "")
        except:
            pass  # Leave patient_name blank

    return render_template("schedule_session.html", patients=patient_list, user=user,
                           prefill_id=patient_id, prefill_name=patient_name,
                           therapist_email=therapist_email)


@calendar_bp.route("/api/therapists_for_patient/<patient_id>")
def therapists_for_patient(patient_id):
    try:
        pid = ObjectId(patient_id)
        patient = patients_collection.find_one({"_id": pid})
    except:
        return {"therapists": []}

    if not patient or "doctor_emails" not in patient:
        return {"therapists": []}

    return {"therapists": patient["doctor_emails"]}
