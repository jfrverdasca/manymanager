from werkzeug.routing import BaseConverter, ValidationError
from datetime import datetime


class DateConverter(BaseConverter):

    regex = r'\d{1,2}-\d{1,2}-\d{4}'

    def to_python(self, value):
        try:
            return datetime.strptime(value, '%d-%m-%Y')

        except ValueError as date_conversion_error:
            raise ValidationError(date_conversion_error)

    def to_url(self, value):
        if isinstance(value, datetime):
            return value.strftime('%d-%m-%Y')

        else:
            return value
