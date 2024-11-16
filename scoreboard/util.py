import smtplib
from email.message import EmailMessage
from typing import Sequence

from flask import current_app


def send_email(recipients: str | Sequence[str], subject: str, body: str):
    if current_app.config["SCOREBOARD_DEVELOPMENT"]:
        return
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = current_app.config["SCOREBOARD_EMAIL_SENDER"]
    if isinstance(recipients, str):
        msg["To"] = recipients
    else:
        msg["To"] = ",".join(recipients)

    try:
        with smtplib.SMTP(
            current_app.config["SCOREBOARD_SMTP_HOST"],
            port=current_app.config["SCOREBOARD_SMTP_PORT"],
        ) as s:
            s.starttls()
            s.login(
                current_app.config["SCOREBOARD_SMTP_USERNAME"],
                current_app.config["SCOREBOARD_SMTP_PASSWORD"],
            )
            s.send_message(msg, to_addrs=recipients)
    except smtplib.SMTPException as ex:
        current_app.logger.error(f"Failed to send email: {type(ex).__name__}: {ex}")
        raise
