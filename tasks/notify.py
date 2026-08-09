import os
from flask import current_app
from flask_mail import Message
from extensions import mail_service

def save_mail_outbox(subject: str, recipients, html_body: str) -> str:
    #Store emails locally when sending is disabled
    outbox_dir = os.path.join(current_app.instance_path, "outbox")
    os.makedirs(outbox_dir, exist_ok=True)
    from datetime import datetime
    fname = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.html"
    path = os.path.join(outbox_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- To: {', '.join(recipients)} | Subject: {subject} -->\n{html_body}")
    return path

def sendEmail(subject: str, recipients, html_body: str):
    if current_app.config.get("MAIL_SUPPRESS_SEND", True):
        path = save_mail_outbox(subject, recipients, html_body)
        return f"suppressed -> written to {path}"
    #Send the email through the configured mail server
    msg = Message(subject=subject, recipients=recipients, html=html_body)
    mail_service.send(msg)
    return "sent"
