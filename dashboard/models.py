from flask import current_app
from flask_login import UserMixin
from sqlalchemy.orm import validates, synonym
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired, BadSignature
from datetime import datetime
from dashboard import db, login_manager


class Share(db.Model):

    __table_args__ = db.PrimaryKeyConstraint('left_id', 'right_id', name='share_pk'),

    left_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))  # me
    right_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))  # others

    shared_by = db.relationship('User', back_populates='shared_by', foreign_keys=[left_id])
    shared_with = db.relationship('User', back_populates='shared_with', foreign_keys=[right_id])

    user = synonym('shared_with')  # to be used in ShareForm

    @staticmethod
    def get_share_request_token(share_with_user_id):
        return TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],
                                               current_app.config['SHARE_TOKEN_EXPIRATION_SECONDS'])\
            .dumps({'share_with_user_id': share_with_user_id})\
            .decode('utf-8')

    @staticmethod
    def check_share_request_token(token):
        try:
            shared_with_user_id = \
                TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY']).loads(token)['share_with_user_id']

        except (SignatureExpired, BadSignature, KeyError):
            return None

        return User.query.filter_by(id=shared_with_user_id, active=True).first()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(15), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean(), default=True)

    # own one-to-many relationships
    shared_by = db.relationship('Share', foreign_keys=Share.left_id)  # me
    shared_with = db.relationship('Share', foreign_keys=Share.right_id)  # others

    # category one-to-many relationship
    categories = db.relationship('Category', back_populates='user')

    # expense one-to-many relationship
    expenses = db.relationship('Expense', back_populates='user')

    # alerts one-to-many relationship
    alerts = db.relationship('Alert', back_populates='user')

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

    def get_password_reset_token(self):
        return TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],
                                               current_app.config['PASSWORD_TOKEN_EXPIRATION_SECONDS'])\
            .dumps({'id': self.id})\
            .decode('utf-8')

    @staticmethod
    def check_password_reset_token(token):
        try:
            user_id = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY']).loads(token)['id']

        except (SignatureExpired, BadSignature, KeyError):
            return None

        return User.query.filter_by(id=user_id, active=True).first()


class Category(db.Model):

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    limit = db.Column(db.Float, default=0)
    color = db.Column(db.String(7), nullable=True)

    # user one-to-many relationship
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='categories')  # reverse many-to-one

    # expenses one-to-many relationship
    expenses = db.relationship('Expense', back_populates='category')

    def __str__(self):
        return str(self.id)


class Expense(db.Model):

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    description = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    value = db.Column(db.Float, default=0)
    is_favorite = db.Column(db.Boolean, default=False)
    favorite_sort = db.Column(db.Integer, nullable=True)

    # user one-to-many relationship
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='expenses')  # reverse many-to-one

    # category one-to-many relationship
    category_id = db.Column(db.BigInteger, db.ForeignKey('category.id'))
    category = db.relationship('Category', back_populates='expenses')  # reverse many-to-one

    # self one-to-one relationship
    parent_id = db.Column(db.BigInteger, db.ForeignKey('expense.id'), nullable=True)
    children = db.relationship('Expense')

    @validates(is_favorite)
    def validate_is_favorite(self, key, is_favorite):
        # update display order only if is_favorite changed it's value
        if self.is_favorite is not None and self.is_favorite != is_favorite:
            self._set_favorite_sort(None, is_favorite)

        return is_favorite

    def set_favorite_sort(self, value):
        self._set_favorite_sort(value, self.is_favorite)

    def _set_favorite_sort(self, value, is_favorite):
        expenses = Expense.query.filter_by(user=self.user, is_favorite=True).order_by('favorite_sort').all()
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
                self.favorite_sort = None

        for i, expense in enumerate(expenses):
            expense.favorite_sort = i

    def copy(self):
        return Expense(description=self.description,
                       timestamp=self.timestamp,
                       value=self.value,
                       is_favorite=self.is_favorite,
                       favorite_sort=self.favorite_sort,
                       user=self.user,
                       category_id=self.category_id,
                       parent_id=self.parent_id)

    def get_child_expenses(self):
        return Expense.query.filter(Expense.parent_id == self.id)


class Alert(db.Model):

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(5000))
    seen = db.Column(db.Boolean, default=False)

    # user one-to-many relationship
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='alerts')
