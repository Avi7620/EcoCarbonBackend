from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app, origins=["https://ecocarbon.onrender.com", "http://localhost:5173"])

DATABASE_URL = os.environ.get("postgresql://ecodatabase_user:NKEY6c4wquO6fEbxk20GEnhibKEqeiYs@dpg-d3cm65adbo4c73ead4s0-a.oregon-postgres.render.com/ecodatabase")

# --- Initialize Postgres Database ---
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


# --- API Route to Fetch All Submissions ---
@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
