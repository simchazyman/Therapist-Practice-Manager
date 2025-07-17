from flask import Blueprint, render_template, request, redirect, session
from bson import ObjectId
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
patients_collection = db["patients"]
users_collection = db["users"]
field_registry_collection = db["custom_field_registry"]  # ✅ new collection

def is_admin_or_secretary():
    user = session.get("user")
    return user and user.get("role") in ["admin", "secretary"]

def get_therapist_list():
    return list(users_collection.find({"role": "therapist"}))

def update_custom_fields(existing_fields, form_data):
    updated = {}
    for key in existing_fields:
        updated[key] = form_data.get(f"custom_{key}", "")
    return updated

def extract_new_custom_fields(form_data):
    custom_fields = {}
    for key in form_data:
        if key.startswith("custom_") and not key.startswith("custom_delete_"):
            actual_key = key.replace("custom_", "")
            value = form_data.get(key, "").strip()
            if actual_key and value:
                custom_fields[actual_key] = value
    return custom_fields

def merge_custom_fields(existing, updates, new_fields):
    updated = existing.copy()
    updated.update(updates)
    updated.update(new_fields)
    return updated

def clean_field(form, key):
    return form.get(key, "").strip()

def safe_object_id(id_str):
    try:
        return ObjectId(id_str)
    except:
        return None

def create_edit_patient_route(bp):
    @bp.route("/edit_patient/<patient_id>", methods=["GET", "POST"])
    def edit_patient(patient_id):
        if not is_admin_or_secretary():
            return redirect("/login")

        oid = safe_object_id(patient_id)
        if not oid:
            return "Invalid ID", 400

        patient = patients_collection.find_one({"_id": oid})
        if not patient:
            return "Patient not found", 404

        if request.method == "POST":
            name = clean_field(request.form, "name")
            dob = clean_field(request.form, "dob")
            phone = clean_field(request.form, "phone")
            email = clean_field(request.form, "email")
            address = clean_field(request.form, "address")
            secretary_note = clean_field(request.form, "secretary_note")


            # Custom field handling
            existing_custom = patient.get("custom_fields", {})
            updated_custom = update_custom_fields(existing_custom, request.form)
            new_custom = extract_new_custom_fields(request.form)

            # ✅ Log new custom fields into registry
            for key in new_custom:
                field_registry_collection.update_one(
                    {"name": key},
                    {"$setOnInsert": {"name": key}},
                    upsert=True
                )

            # Merge fields and remove deleted ones
            merged_fields = merge_custom_fields(existing_custom, updated_custom, new_custom)
            deleted_keys = [k.replace("delete_custom_", "") for k in request.form if k.startswith("delete_custom_")]
            custom_fields = {
                k: v for k, v in merged_fields.items()
                if k not in deleted_keys and v.strip()
            }

            patients_collection.update_one(
                {"_id": oid},
                {"$set": {
                    "name": name,
                    "dob": dob,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "secretary_note": secretary_note,
                    "custom_fields": custom_fields
                }}
            )

            return redirect(f"/patient/{patient_id}")


        therapists = get_therapist_list()

        if "custom_fields" not in patient:
            patient["custom_fields"] = {}

        # ✅ Load all previous field names
        field_names = [doc["name"] for doc in field_registry_collection.find()]

        return render_template("edit_patient.html", patient=patient, therapists=therapists, field_names=field_names)
