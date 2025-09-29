from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from emailService import init_mail, send_otp_email, verify_otp, mail

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "your-secret-key"
CORS(app, origins=["https://ecocarbon.onrender.com", "http://localhost:5173"], supports_credentials=True)

# --- Database Config ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

# --- Mail Config ---
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")  # Your Gmail
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")  # App Password
init_mail(app)

# --- DB Init ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            service TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# ======================
# API 1: Save Contact Form
# ======================
@app.route("/api/contact", methods=["POST"])
def save_contact():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    company = data.get("company", "")
    phone = data.get("phone", "")
    service = data.get("service", "")
    message = data.get("message")

    if not name or not email or not message:
        return jsonify({"error": "Missing required fields"}), 400

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contacts (name, email, company, phone, service, message)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, email, company, phone, service, message))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Form submitted successfully!"}), 201

# ======================
# API 2: Get Contacts (Admin Only)
# ======================
@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# ======================
# API 3: Send OTP (Admin Login)
# ======================
@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")

    if email != "jadhavaj7620@gmail.com":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        send_otp_email(email)
        return jsonify({"message": "OTP sent to email"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================
# API 4: Verify OTP
# ======================
@app.route("/api/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    success, msg = verify_otp(email, otp)
    if success:
        session["admin"] = True
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": msg}), 400

# ======================
# API 5: Admin Dashboard
# ======================
@app.route("/api/admin-dashboard", methods=["GET"])
def admin_dashboard():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({"message": "Welcome to Admin Dashboard"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))