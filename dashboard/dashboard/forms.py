from flask_wtf import FlaskForm
from wtforms import validators, DateField, TimeField, SelectField, StringField, FloatField, BooleanField, SubmitField
from datetime import datetime


class ExpenseForm(FlaskForm):

    description = StringField('Description', validators=[validators.DataRequired()])
    category = SelectField('Category', validators=[validators.DataRequired()])
    date = DateField('Date', format='%d-%m-%Y', default=datetime.now().date(), validators=[validators.DataRequired()])
    time = TimeField('Time', format='%H:%M:%S', default=datetime.now().time(), validators=[validators.DataRequired()])
    value = FloatField('Value', default=0, validators=[validators.DataRequired(), validators.NumberRange(min=0)])
    is_favorite = BooleanField('Favorite', default=False, validators=[validators.Optional()])
    submit = SubmitField('Save')


# generic entity delete form
class DeleteForm(FlaskForm):

    submit = SubmitField('Delete')
