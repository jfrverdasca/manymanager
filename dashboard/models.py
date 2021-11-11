from flask import current_app
from flask_login import UserMixin
from sqlalchemy.orm import validates
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired, BadSignature
from datetime import datetime
from dashboard import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    expenses = db.relationship('Expense', backref='user', lazy=True)

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def get_password_reset_token(self, expires_seconds=1800):
        return TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_seconds)\
            .dumps({'id': self.id})\
            .decode('utf-8')

    @staticmethod
    def check_password_reset_token(token):
        try:
            user_id = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY']).loads(token)['id']

        except (SignatureExpired, BadSignature):
            return None

        return User.query.get(user_id)


class Category(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(500), nullable=True)
    limit = db.Column(db.Float, default=0)
    color = db.Column(db.String(7), nullable=True)
    owner = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __str__(self):
        return f'{self.id}'


class Expense(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    description = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    value = db.Column(db.Float, default=0)
    is_favorite = db.Column(db.Boolean, default=False)
    favorite_order = db.Column(db.Integer, nullable=True)
    owner = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.BigInteger, db.ForeignKey('category.id'), nullable=False)

    @validates('is_favorite')
    def validate_is_favorite(self, key, is_favorite):
        # update display order only if is_favorite changed it's value
        if self.is_favorite is not None and self.is_favorite != is_favorite:
            self._set_favorite_order(None, is_favorite)

        return is_favorite

    def set_favorite_order(self, value):
        self._set_favorite_order(value, self.is_favorite)

    def _set_favorite_order(self, value, is_favorite):
        expenses = Expense.query.filter_by(owner=self.owner, is_favorite=True).order_by('favorite_order').all()
        if value is not None and value >= 0:
            expenses.insert(value, expenses.pop(expenses.index(self)))

        elif is_favorite:
            expenses.append(self)

        else:
            try:
                expenses.remove(self)

            except ValueError:
                return

            else:
                self.favorite_order = None

        for i, expense in enumerate(expenses):
            expense.favorite_order = i
