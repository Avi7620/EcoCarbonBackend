from flask_mail import Mail, Message
import time
import random

mail = Mail()  # Create Mail object, but don't initialize yet

# OTP storage (in-memory)
otp_storage = {}  # { email: {otp: 123456, expires: 1696000000} }

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        raise Exception("MAIL_USERNAME or MAIL_PASSWORD not set in app.config")
    mail.init_app(app)  # Now mail.app is set

def send_otp_email(email):
    """Generate and send OTP to the given email"""
    if not mail.app:
        raise Exception("Mail is not initialized. Call init_mail(app) first.")

    otp = random.randint(100000, 999999)
    otp_storage[email] = {"otp": otp, "expires": time.time() + 300}  # 5 min expiry

    msg = Message(
        subject="Your Admin OTP",
        sender=mail.app.config["MAIL_USERNAME"],
        recipients=[email]
    )
    msg.body = f"Your OTP is {otp}. It will expire in 5 minutes."
    mail.send(msg)
    return otp

def verify_otp(email, otp):
    """Verify OTP for the given email"""
    record = otp_storage.get(email)
    if not record:
        return False, "OTP not requested"
    if time.time() > record["expires"]:
        return False, "OTP expired"
    if str(record["otp"]) == str(otp):
        return True, "OTP verified"
    return False, "Invalid OTP"
