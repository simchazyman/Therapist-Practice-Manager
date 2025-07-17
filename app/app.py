from flask import Flask, session, redirect
from assign_therapist import assign_bp
from pymongo import MongoClient
import os
from auth import auth_bp
from config import MONGO_URI, DB_NAME  # Import MongoDB config
from calendar_routes import calendar_bp
from patients import patients_bp
from admin import admin_bp
from secretary import secretary_bp
from therapist_admin_routes import therapist_admin_bp



# Flask Setup
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Setup - Now using values from config.py
client = MongoClient(MONGO_URI)  # Connect to MongoDB using the URI from config.py
db = client[DB_NAME]  # Use the database name from config.py

# Register Blueprint


app.register_blueprint(auth_bp)

app.register_blueprint(calendar_bp)

app.register_blueprint(patients_bp)

app.register_blueprint(admin_bp)

app.register_blueprint(secretary_bp)

app.register_blueprint(assign_bp)

app.register_blueprint(therapist_admin_bp)

from therapist_patient_view import therapist_view_bp
app.register_blueprint(therapist_view_bp)








# Home Page
@app.route("/")
def home():
    user = session.get("user")
    if not user:
        return redirect("/login")

    if user["role"] == "therapist":
        return redirect("/dashboard")
    elif user["role"] == "admin":
        return redirect("/admin")
    elif user["role"] == "secretary":
        return redirect("/secretary")
    else:
        return redirect("/waiting_for_approval")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")




# Run Flask App with Fake HTTPS
if __name__ == "__main__":
    app.run(ssl_context="adhoc", debug=True)
