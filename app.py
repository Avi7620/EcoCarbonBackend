from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)


# --- Security ---
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret_local_key")

# --- Database Config ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set!")

# --- SendGrid Config ---
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")   # set in Render
EMAIL_ADDRESS = os.getenv("SENDGRID_FROM_EMAIL")   # verified sender in SendGrid

# --- CORS ---
CORS(
    app,
    origins=[
        
        "https://ecocarbon.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "https://ecarbon5.onrender.com"
    ],
    supports_credentials=True
)

app.config.update(
    SESSION_COOKIE_SAMESITE=None,
    SESSION_COOKIE_SECURE=False,  # Change to True in production
    SESSION_COOKIE_HTTPONLY=True
)

# --- Init DB ---
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

# --- OTP Store ---
otp_store = {}

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# --- Send Email ---
def send_email(to_email, otp):
    try:
        message = Mail(
            from_email=EMAIL_ADDRESS,
            to_emails=to_email,
            subject="EcoCarbon Admin Login OTP",
            plain_text_content=f"Your OTP for EcoCarbon Admin Login is: {otp}"
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print("Email sent:", response.status_code)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

# --- Routes ---
@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    allowed_admins = [os.getenv("ADMIN_EMAIL", "jadhavavi7620@gmail.com")]
    if email not in allowed_admins:
        return jsonify({"error": "Unauthorized email"}), 403

    otp = generate_otp()
    otp_store[email] = otp

    if send_email(email, otp):
        return jsonify({"message": "OTP sent successfully"})
    else:
        return jsonify({"error": "Failed to send OTP"}), 500

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    if email in otp_store and otp_store[email] == otp:
        session["admin"] = email
        otp_store.pop(email)
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid OTP"}), 400

def require_admin():
    return "admin" in session

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

@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    # if not require_admin():
    #     return jsonify({"error": "Unauthorized"}), 401

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/session', methods=['GET'])
def session_status():
    admin = session.get('admin')
    if admin:
        return jsonify({'admin': admin})
    else:
        return jsonify({'admin': None}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
