from flask_mail import Message
from smtplib import SMTPException
from dashboard import mail


def send_email(recipients, subject, body, is_html_body=False):
    if not isinstance(recipients, list):
        recipients = [recipients]

    if is_html_body:
        message = Message(subject, recipients=recipients, html=body, sender='noreply@manymanager.com')

    else:
        message = Message(subject, recipients=recipients, body=body, sender='noreply@manymanager.com')

    try:
        mail.connect()
        mail.send(message)

    except SMTPException as smtp_error:
        print(smtp_error)
