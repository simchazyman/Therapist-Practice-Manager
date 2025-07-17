# Flask Therapy Management App

This is a Flask-based web application designed to help manage patient information, session scheduling, and note-taking for a therapy practice. It integrates with MongoDB for data storage, Google OAuth for authentication, and Google Docs and Calendar APIs for document and scheduling management.

---

## 🚀 Features

- User authentication with **Google OAuth**
- Role-based access control with different permission levels (e.g., administrator, therapist, secretary)
- Dynamic display of information tailored to the logged-in user’s role
- Integration with **MongoDB** to store patient records and session data
- Google Docs integration for session note management
- Google Calendar integration for scheduling sessions
- Configurable via a `config.py` file (excluded from the repository for privacy)

---

## ⚙️ Requirements

- Python 3.8 or higher
- MongoDB instance accessible via connection URI
- Google API credentials for OAuth, Docs, and Calendar
- Administrator email configured for access control

