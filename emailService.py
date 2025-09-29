from flask import current_app
from flask_mail import Mail, Message
import time
import random

# Create Mail object (uninitialized)
mail = Mail()

# OTP storage (in-memory)
otp_storage = {}  # { email: {otp: 123456, expires: 1696000000} }

def init_mail(app):
    """
    Initialize Flask-Mail with app configuration.
    Ensure MAIL_USERNAME and MAIL_PASSWORD are set in environment/app.config
    """
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        raise Exception("MAIL_USERNAME or MAIL_PASSWORD not set in app.config")
    mail.init_app(app)  # Attach app to mail

def send_otp_email(email):
    """
    Generate and send OTP to the given email.
    Wraps in current_app context to ensure mail.app is available.
    """
    app = current_app._get_current_object()
    if not mail.app:
        mail.init_app(app)  # Initialize if somehow not done

    # Generate OTP
    otp = random.randint(100000, 999999)
    otp_storage[email] = {"otp": otp, "expires": time.time() + 300}  # 5 min expiry

    # Create and send email
    msg = Message(
        subject="Your Admin OTP",
        sender=app.config["MAIL_USERNAME"],
        recipients=[email]
    )
    msg.body = f"Your OTP is {otp}. It will expire in 5 minutes."
    mail.send(msg)
    return otp

def verify_otp(email, otp):
    """
    Verify OTP for the given email
    """
    record = otp_storage.get(email)
    if not record:
        return False, "OTP not requested"
    if time.time() > record["expires"]:
        return False, "OTP expired"
    if str(record["otp"]) == str(otp):
        return True, "OTP verified"
    return False, "Invalid OTP"
