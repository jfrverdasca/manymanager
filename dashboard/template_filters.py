from flask import current_app
from datetime import datetime


@current_app.template_filter('formatdatetime')
def format_datetime(value):
    format_str = current_app.config['DATETIME_FORMAT']

    if isinstance(value, str):
        return datetime.strptime(value, format_str)

    return value.strftime(format_str)


@current_app.template_filter('timeagostr')
def time_ago_str(value):
    format_str = current_app.config['DATETIME_FORMAT']

    if isinstance(value, str):
        value = datetime.strptime(value, format_str)

    past_timedelta = (datetime.now() - value)

    years_ago = int(past_timedelta.days / 365)
    if years_ago > 0:
        return f'{years_ago} years ago'

    months_ago = int(past_timedelta.days / 30)
    if months_ago > 0:
        return f'{months_ago} months ago'

    if past_timedelta.days > 0:
        return f'{past_timedelta.days} days ago'

    hours_ago = int(past_timedelta.seconds / 3600)
    if hours_ago > 0:
        return f'{hours_ago} hours ago'

    minutes_ago = int(past_timedelta.seconds / 60)
    if minutes_ago > 0:
        return f'{minutes_ago} minutes ago'

    return f'{past_timedelta.seconds} seconds ago'
