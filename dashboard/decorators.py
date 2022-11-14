from flask import abort
from flask_login import current_user
from functools import wraps


def login_required_401(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        return f(*args, **kwargs)
    return wrapper
