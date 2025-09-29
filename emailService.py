from flask_mail import Mail, Message
import time
import random

mail = Mail()  # Mail object
otp_storage = {}  # { email: {otp: 123456, expires: timestamp} }

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    # Use the values already set in app.config
    mail.init_app(app)

def send_otp_email(app, email):
    """Generate and send OTP to the given email"""
    otp = random.randint(100000, 999999)
    otp_storage[email] = {"otp": otp, "expires": time.time() + 300}  # 5 min expiry

    msg = Message(
        "Your Admin OTP",
        sender=app.config["MAIL_USERNAME"],
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
