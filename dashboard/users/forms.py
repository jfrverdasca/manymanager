from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, SubmitField, BooleanField, ValidationError
from dashboard.models import User


class RegisterForm(FlaskForm):

    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    username = StringField('Username', validators=[validators.DataRequired(), validators.Length(min=5, max=15)])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    password_confirmation = PasswordField('Password confirmation', validators=[validators.DataRequired(),
                                                                               validators.EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('There is already a registered user with this email')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('There is already a registered user with this username')


class LoginForm(FlaskForm):
    email_username = StringField('Username/Email', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    remember = BooleanField('Remember')
    submit = SubmitField('Login')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    submit = SubmitField('Send email')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('There is no account with this email address')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[validators.DataRequired()])
    password_confirmation = PasswordField('Password confirmation', validators=[validators.DataRequired(),
                                                                               validators.EqualTo('password')])
    submit = SubmitField('Reset password')
