from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import os
app = Flask(__name__)
#CORS(app)  # local development
CORS(app, origins=["https://ecocarbon.onrender.com", "http://localhost:5173"])  # production


# --- Initialize SQLite Database ---
def init_db():
    conn = sqlite3.connect("contact.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.close()

init_db()

# --- API Route to Save Form Data ---
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

    conn = sqlite3.connect("contact.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contacts (name, email, company, phone, service, message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, company, phone, service, message))
    conn.commit()
    conn.close()

    return jsonify({"message": "Form submitted successfully!"}), 201


# --- API Route to Fetch All Submissions (for dashboard) ---
@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    conn = sqlite3.connect("contact.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    contacts = [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "company": row[3],
            "phone": row[4],
            "service": row[5],
            "message": row[6],
            "created_at": row[7]  # timestamp of submission
        }
        for row in rows
    ]

    return jsonify(contacts)


# if __name__ == "__main__":
#     app.run(debug=True)       #local development

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

