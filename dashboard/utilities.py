from flask_mail import Message
from dashboard import mail


def send_email(recipients, subject, body, is_html_body=False):
    if not isinstance(recipients, list):
        recipients = [recipients]

    if is_html_body:
        message = Message(subject, recipients=recipients, html=body, sender='noreply@manymanager.com')

    else:
        message = Message(subject, recipients=recipients, body=body, sender='noreply@manymanager.com')

    mail.send(message)
