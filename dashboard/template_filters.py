from flask import current_app
from datetime import datetime


@current_app.template_filter('formatdatetime')
def format_datetime(value):
    format_str = current_app.config['DATETIME_FORMAT']

    if isinstance(value, str):
        return datetime.strptime(value, format_str)

    return value.strftime(format_str)
