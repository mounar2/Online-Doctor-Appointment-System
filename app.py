import os
import json
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_in_env")

# ------------------------------
# FILE PATHS
# ------------------------------
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
APPTS_FILE = os.path.join(DATA_DIR, "appointments.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

os.makedirs(DATA_DIR, exist_ok=True)
for file in [USERS_FILE, APPTS_FILE, MESSAGES_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f, indent=4)

# ------------------------------
# JSON HELPERS
# ------------------------------
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------------------
# USER HELPERS
# ------------------------------
def find_user_by_id(uid):
    users = load_json(USERS_FILE)
    return next((u for u in users if u["id"] == uid), None)

def find_user_by_email(email):
    users = load_json(USERS_FILE)
    email = (email or "").lower()
    return next((u for u in users if u["email"].lower() == email), None)

def ensure_admin_created():
    users = load_json(USERS_FILE)
    if any(u["role"] == "admin" for u in users):
        return
    admin = {
        "id": str(uuid.uuid4()),
        "name": "Admin",
        "email": "admin@example.com",
        "password_hash": generate_password_hash("admin123"),
        "role": "admin",
        "specialty": "",
        "phone": ""
    }
    users.append(admin)
    save_json(USERS_FILE, users)

# ------------------------------
# LOGIN REQUIRED DECORATOR
# ------------------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first.", "warning")
                return redirect(url_for("login_page"))
            if role and session.get("role") != role:
                return "Forbidden", 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ------------------------------
# ROUTES
# ------------------------------
@app.route("/about")
def about_page():
    return render_template("about.html")
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    messages = load_json(MESSAGES_FILE)  # تعريف messages دائماً قبل أي شيء
    success_msg = None

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if name and email and message:
            messages.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "email": email,
                "message": message,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_json(MESSAGES_FILE, messages)
            success_msg = "Message sent successfully!"
        else:
            success_msg = "Please fill all fields."

    return render_template("contact.html", success_msg=success_msg)



# ------------------------------
# LOGIN & REGISTER
# ------------------------------
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email")
    password = request.form.get("password")
    user = find_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid credentials", "danger")
        return redirect(url_for("login_page"))
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]
    if user["role"] == "patient":
        return redirect(url_for("patient_dashboard"))
    if user["role"] == "doctor":
        return redirect(url_for("doctor_dashboard"))
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html")
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    phone = request.form.get("phone", "")
    specialty = request.form.get("specialty", "") if role == "doctor" else ""
    if not password or len(password) < 6:
        flash("Password must be at least 6 characters.", "warning")
        return redirect(url_for("register_page"))
    if find_user_by_email(email):
        flash("Email already used.", "danger")
        return redirect(url_for("register_page"))
    new_user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "role": role,
        "specialty": specialty,
        "phone": phone
    }
    users = load_json(USERS_FILE)
    users.append(new_user)
    save_json(USERS_FILE, users)
    flash("Account created! Please login.", "success")
    return redirect(url_for("login_page"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# ------------------------------
# DASHBOARDS
# ------------------------------
@app.route("/patient")
@login_required(role="patient")
def patient_dashboard():
    my_id = session.get("user_id")
    appts = load_json(APPTS_FILE)
    users = load_json(USERS_FILE)
    my_appts = []
    for a in appts:
        if a.get("patient_id") == my_id:
            doctor = find_user_by_id(a.get("doctor_id"))
            my_appts.append({
                "id": a.get("id"),
                "doctor_name": doctor["name"] if doctor else "",
                "doctor_specialty": doctor["specialty"] if doctor else "",
                "date": a.get("date"),
                "reason": a.get("reason"),
                "status": a.get("status", "pending")
            })
    doctors = [u for u in users if u.get("role") == "doctor"]
    return render_template("patient_dashboard.html", doctors=doctors, appointments=my_appts)

@app.route("/doctor")
@login_required(role="doctor")
def doctor_dashboard():
    my_id = session["user_id"]
    appts = load_json(APPTS_FILE)
    my_appts = [a for a in appts if a["doctor_id"] == my_id]
    for a in my_appts:
        a["patient"] = find_user_by_id(a["patient_id"])
    return render_template("doctor_dashboard.html", appointments=my_appts)

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    users = load_json(USERS_FILE)
    appts = load_json(APPTS_FILE)
    messages = load_json(MESSAGES_FILE)
    for a in appts:
        a["patient"] = find_user_by_id(a["patient_id"])
        a["doctor"] = find_user_by_id(a["doctor_id"])
    return render_template("admin_dashboard.html", users=users, appointments=appts, messages=messages)

# ------------------------------
# ADMIN FUNCTIONS
# ------------------------------
@app.route("/admin/create_user", methods=["POST"])
@login_required(role="admin")
def create_user():
    data = request.form
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    phone = data.get("phone", "")
    specialty = data.get("specialty", "") if role == "doctor" else ""
    if not name or not email or not password or not role:
        flash("All fields are required.", "warning")
        return redirect(url_for("admin_dashboard"))
    if find_user_by_email(email):
        flash("Email already exists.", "danger")
        return redirect(url_for("admin_dashboard"))
    new_user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "role": role,
        "specialty": specialty,
        "phone": phone
    }
    users = load_json(USERS_FILE)
    users.append(new_user)
    save_json(USERS_FILE, users)
    flash(f"User {name} created successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit_user/<user_id>", methods=["POST"])
@login_required(role="admin")
def edit_user(user_id):
    users = load_json(USERS_FILE)
    user = find_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    data = request.form
    user["name"] = data.get("name", user["name"])
    user["email"] = data.get("email", user["email"])
    password = data.get("password")
    if password:
        user["password_hash"] = generate_password_hash(password)
    user["role"] = data.get("role", user["role"])
    user["phone"] = data.get("phone", user.get("phone", ""))
    if user["role"] == "doctor":
        user["specialty"] = data.get("specialty", user.get("specialty", ""))
    else:
        user["specialty"] = ""
    save_json(USERS_FILE, users)
    flash(f"User {user['name']} updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_user/<user_id>", methods=["POST"])
@login_required(role="admin")
def delete_user(user_id):
    users = load_json(USERS_FILE)
    user = find_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    users = [u for u in users if u["id"] != user_id]
    save_json(USERS_FILE, users)
    flash(f"User {user['name']} deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_appointment/<appt_id>", methods=["POST"])
@login_required(role="admin")
def delete_appointment(appt_id):
    appts = load_json(APPTS_FILE)
    appt = next((a for a in appts if a["id"] == appt_id), None)
    if not appt:
        flash("Appointment not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    appts = [a for a in appts if a["id"] != appt_id]
    save_json(APPTS_FILE, appts)
    flash("Appointment deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))

# ------------------------------
# START APP
# ------------------------------
ensure_admin_created()

if __name__ == "__main__":
    app.run(debug=True)
