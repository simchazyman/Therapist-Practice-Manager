from googleapiclient.discovery import build


from googleapiclient.discovery import build

def ensure_notes_doc_for_patient(creds, patient_id, patient_name, patients_collection):
    patient = patients_collection.find_one({"_id": patient_id})
    if not patient:
        raise ValueError("Patient not found")

    # If already created and stored, reuse it
    if patient.get("notes_doc_id"):
        doc_id = patient["notes_doc_id"]
        return {
            "id": doc_id,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit"
        }

    # Create new doc
    docs_service = build("docs", "v1", credentials=creds)
    doc_title = f"Session Notes – {patient_name}"
    doc = docs_service.documents().create(body={"title": doc_title}).execute()
    doc_id = doc["documentId"]

    # Save to patient document
    patients_collection.update_one(
        {"_id": patient_id},
        {"$set": {"notes_doc_id": doc_id}}
    )

    return {
        "id": doc_id,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit"
    }
