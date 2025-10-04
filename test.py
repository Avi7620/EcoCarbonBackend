from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)


app.secret_key = "supersecret_local_key"   # manually set secret key
DATABASE_URL = "postgresql://ecodatabase_user:NKEY6c4wquO6fEbxk20GEnhibKEqeiYs@dpg-d3cm65adbo4c73ead4s0-a.oregon-postgres.render.com/ecodatabase"
EMAIL_ADDRESS = "jadhavavi7620@gmail.com"
EMAIL_PASSWORD = "pfwhfzhxcucbcoiy"

CORS(
    app,
    origins=["https://ecocarbon.onrender.com", "http://localhost:5173", "http://localhost:3000", "http://localhost:3001","https://ecarbon5.onrender.com"],
    supports_credentials=True
)
app.config.update(
    SESSION_COOKIE_SAMESITE="None",  # cross-site for local testing
    SESSION_COOKIE_SECURE=False,     # True if using HTTPS
    SESSION_COOKIE_HTTPONLY=True
)

# --- Database ---

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

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


# Store OTPs temporarily (in-memory for demo)
otp_store = {}

# --- Generate OTP ---
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# --- Send OTP Email ---
def send_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = "EcoCarbon Admin Login OTP"

        body = f"Your OTP for EcoCarbon Admin Login is: {otp}"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False


# --- API: Send OTP ---
@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    # Only allow specific admin emails
    allowed_admins = ["jadhavaj7620@gmail.com"]  # <-- change to your admin emails
    if email not in allowed_admins:
        return jsonify({"error": "Unauthorized email"}), 403

    otp = generate_otp()
    otp_store[email] = otp

    if send_email(email, otp):
        return jsonify({"message": "OTP sent successfully"})
    else:
        return jsonify({"error": "Failed to send OTP"}), 500


# --- API: Verify OTP ---
@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    if email in otp_store and otp_store[email] == otp:
        session["admin"] = email  # Store session
        otp_store.pop(email)  # Remove OTP once verified
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid OTP"}), 400


# --- Middleware: Protect Admin Routes ---
def require_admin():
    if "admin" not in session:
        return False
    return True


# --- API: Save Contact ---
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


# --- API: Fetch All Contacts (Admin Only) ---
@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 401

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


# --- API: Logout ---
@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"message": "Logged out successfully"})


@app.route('/api/session', methods=['GET'])
def session_status():
    """Return current admin session status for frontend verification."""
    admin = session.get('admin')
    if admin:
        return jsonify({'admin': admin})
    else:
        return jsonify({'admin': None}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
