from flask_wtf import FlaskForm
from wtforms import validators, widgets, DateField, TimeField, \
    SelectField, StringField, FloatField, BooleanField, SubmitField


class ExpenseForm(FlaskForm):

    description = StringField('Description', validators=[validators.DataRequired(), validators.Length(max=50)])
    category = SelectField('Category', validators=[validators.DataRequired()])
    date = DateField('Date', widget=widgets.TextInput(), format='%d-%m-%Y',
                     validators=[validators.DataRequired()])  # datetime widget does not work properly in some browsers
    time = TimeField('Time', format='%H:%M:%S', validators=[validators.DataRequired()])
    value = FloatField('Value', default=0, validators=[validators.DataRequired(), validators.NumberRange(min=0)])
    is_favorite = BooleanField('Favorite', default=False, validators=[validators.Optional()])
    submit = SubmitField('Save')


class CategoryForm(FlaskForm):

    name = StringField('Name', validators=[validators.DataRequired(), validators.Length(max=50)])
    limit = FloatField('Limit', default=0, validators=[validators.InputRequired(), validators.NumberRange(min=0)])
    color = StringField('Color', validators=[validators.DataRequired(), validators.Length(min=7, max=7)])
    submit = SubmitField('Save')


# generic entity delete form
class DeleteForm(FlaskForm):

    submit = SubmitField('Delete')
