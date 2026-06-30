import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def send_qr_email(recipient_email, recipient_name, qr_bytes):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    if not sender_email or not sender_password:
        return False

    try:
        msg = MIMEMultipart()
        msg["Subject"] = "JARVIS // Secure Access Credential"
        msg["From"] = sender_email
        msg["To"] = recipient_email
        html = f"""
        <html><body style="background-color:#03080c; color:#00f3ff; font-family:Courier New, monospace;">
            <h2>SECURE ACCESS GRANTED</h2>
            <p>Subject: {recipient_name}</p>
            <p>Your biometric profile is active. Use the attached cryptographic QR for facility access.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))
        msg.attach(MIMEImage(qr_bytes, name="ACCESS_KEY.png"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception:
        return False
