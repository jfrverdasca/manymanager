from flask_mail import Message
from smtplib import SMTPException
from dashboard import mail
from dashboard.models import Expense, Category


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


def get_expenses_by_date_interval_category(user, from_date, to_date, category_id=None):

    if category_id:
        return Expense.query.filter(Expense.user == user,
                                    Expense.timestamp >= from_date,
                                    Expense.timestamp <= to_date,
                                    Expense.category_id == category_id) \
            .join(Category, Expense.category_id == Category.id)

    return Expense.query.filter(Expense.user == user,
                                Expense.timestamp >= from_date,
                                Expense.timestamp <= to_date) \
        .join(Category, Expense.category_id == Category.id)
