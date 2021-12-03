from flask_wtf import FlaskForm
from wtforms import validators, widgets, DateField, TimeField, SelectField, StringField, FloatField, BooleanField, SubmitField
from datetime import datetime


class ExpenseForm(FlaskForm):

    description = StringField('Description', validators=[validators.DataRequired(), validators.Length(max=500)])
    category = SelectField('Category', validators=[validators.DataRequired()])
    date = DateField('Date', widget=widgets.TextInput(), format='%d-%m-%Y', default=datetime.now().date(),
                     validators=[validators.DataRequired()])  # datetime widget does not work properly in some browsers
    time = TimeField('Time', format='%H:%M:%S', default=datetime.now().time(), validators=[validators.DataRequired()])
    value = FloatField('Value', default=0, validators=[validators.DataRequired(), validators.NumberRange(min=0)])
    is_favorite = BooleanField('Favorite', default=False, validators=[validators.Optional()])
    submit = SubmitField('Save')


class CategoryForm(FlaskForm):

    name = StringField('Name', validators=[validators.DataRequired(), validators.Length(max=50)])
    description = StringField('Description', widget=widgets.TextArea(), validators=[validators.Length(max=500)])
    limit = FloatField('Limit', default=0, validators=[validators.DataRequired(), validators.NumberRange(min=0)])
    color = StringField('Color', validators=[validators.DataRequired(), validators.Length(min=7, max=7)])
    submit = SubmitField('Save')


# generic entity delete form
class DeleteForm(FlaskForm):

    submit = SubmitField('Delete')
