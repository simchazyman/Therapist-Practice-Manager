from flask import Blueprint, jsonify, session, redirect, render_template, request
from pymongo import MongoClient
from bson import ObjectId
from config import MONGO_URI, DB_NAME, PROTECTED_ADMINS
from edit_patient_route import create_edit_patient_route


admin_bp = Blueprint("admin", __name__)

# Setup MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
patients_collection = db["patients"]

create_edit_patient_route(admin_bp)


from utils import refresh_session

@admin_bp.route("/admin")
def admin_dashboard():
    user = refresh_session()
    if not user or user["role"] != "admin":
        return redirect("/login")

    all_users = list(users_collection.find({}))
    approved_users = [u for u in all_users if u.get("approved", False)]
    therapists = [u for u in approved_users if u["role"] == "therapist"]
    secretaries = [u for u in approved_users if u["role"] == "secretary"]
    admins = [u for u in approved_users if u["role"] == "admin"]

    patients = patients_collection.find()
    
    pending_users = [u for u in all_users if not u.get("approved", False)]
    approved_users = [u for u in all_users if u.get("approved", False)]

    return render_template("admin_dashboard.html",
        user=user,
        therapists=therapists,
        secretaries=secretaries,
        admins=admins,
        patients=patients,
        pending_users=pending_users,
        protected_admins=PROTECTED_ADMINS
    )








@admin_bp.route("/edit_user/<user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if "user" not in session or session["user"]["role"] != "admin":
        return redirect("/login")

    user_to_edit = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_to_edit:
        return "User not found", 404

    if user_to_edit["email"] in PROTECTED_ADMINS or user_to_edit["email"] == session["user"]["email"]:
        return "You are not allowed to edit this user.", 403

    if request.method == "POST":
        if request.form.get("action") == "delete":
            users_collection.delete_one({"_id": ObjectId(user_id)})
            return redirect("/admin")

        new_role = request.form.get("role")
        new_specialization = request.form.get("specialization", "")
        
        # ✅ If there's no checkbox, keep existing approval status
        approved_flag = user_to_edit.get("approved", False)

        update_fields = {
            "role": new_role,
            "approved": approved_flag,
            "specialization": new_specialization if new_role == "therapist" else ""
        }

        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

        return redirect("/admin")

    return render_template("edit_user.html", user=user_to_edit)








@admin_bp.route("/api/approve_user", methods=["POST"])
def api_approve_user():
    from utils import refresh_session
    user = refresh_session()
    if not user or user["role"] != "admin":

        return jsonify({"success": False, "error": "Not authorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    role = data.get("role")
    specialization = data.get("specialization", "")

    if not user_id or not role:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user["email"] in PROTECTED_ADMINS:
        return jsonify({"success": False, "error": "Cannot modify protected admin"}), 403

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "role": role,
            "approved": True,
            "specialization": specialization if role == "therapist" else ""
        }}
    )

    return jsonify({"success": True})



@admin_bp.route("/api/pending_users")
def api_pending_users():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify([])

    all_users = list(users_collection.find({}))
    pending = [u for u in all_users if not u.get("approved", False)]

    return jsonify([
        {
            "id": str(u["_id"]),
            "name": u["name"],
            "email": u["email"]
        }
        for u in pending
    ])
