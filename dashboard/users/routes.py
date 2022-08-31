import logging

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import RegisterForm, LoginForm, RequestPasswordResetForm, PasswordResetForm
from dashboard.utilities import send_email
from dashboard.models import db, User, Share

logger = logging.getLogger(__name__)

users_blueprint = Blueprint('auth', __name__)


@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()

        flash(f'Account successfully created for {user.email}', 'success')
        return redirect(url_for('auth.login'))

    return render_template('users/register.html', title='Login', form=form)


@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(or_(User.email == form.email_username.data,
                                     User.username == form.email_username.data)).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.home'))

        else:
            flash('Invalid authentication credentials', 'danger')

    return render_template('users/login.html', form=form)


@users_blueprint.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@users_blueprint.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email(user.email, 'ManyManager: Password reset',
                       f'''To reset your password, visit the following link:
                       {url_for('auth.password_reset', token=user.get_password_reset_token(), _external=True)}
                       If you did not make this request please ignore this message''')
            return redirect(url_for('auth.request_password_reset_confirmation'))

    return render_template('users/request_password_reset.html', form=form)


@users_blueprint.route('/request-password-reset-confirmation', methods=['GET'])
def request_password_reset_confirmation():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    return render_template('users/request_password_reset_confirmation.html')


@users_blueprint.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    user = User.check_password_reset_token(token)
    if not user:
        flash('Invalid or expired password reset token', 'danger')
        return redirect(url_for('auth.request_password_reset'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()

        flash('Password has been successfully reset', 'success')
        return redirect(url_for('auth.login'))

    return render_template('users/password_reset.html', form=PasswordResetForm())


@users_blueprint.route('/share-with-user/<token>', methods=['GET', 'POST'])
@login_required
def share_with_user(token):
    user = User.check_share_with_token(token)
    if not user:
        flash('Invalid or expired request sharing permission token', 'danger')

    else:
        db.session.add(Share(shared_by=user, shared_with=current_user))
        db.session.commit()

        flash(f'User {user.username} can now share expenses with you', 'success')

    return redirect(url_for('dashboard.home'))
