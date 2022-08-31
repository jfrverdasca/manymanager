from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from datetime import datetime
from calendar import monthrange
from dashboard.models import Expense, Category, Alert

dashboard_blueprint = Blueprint('dashboard', __name__)


# TODO: test shared expenses marked as favorite

# ajax
@dashboard_blueprint.route('/favorites-list', methods=['GET'])
def favorites_list():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/favorites_list.html',
                           favorites=Expense.query.filter_by(user=current_user, is_favorite=True)
                           .join(Category, Expense.category_id == Category.id)
                           .order_by(Expense.favorite_sort)
                           .all())


@dashboard_blueprint.route('/alerts-list', methods=['GET'])
def alerts_list():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/alerts_list.html',
                           alerts=Alert.query.filter_by(user=current_user, seen=False).all())


# pages
@dashboard_blueprint.route('/', methods=['GET'])
@dashboard_blueprint.route('/index', methods=['GET'])
@dashboard_blueprint.route('/home', methods=['GET'])
@login_required
def home():
    datetime_now = datetime.now()
    _, end_month_day = monthrange(datetime_now.year, datetime_now.month)

    data = {'categories': Category.query.filter_by(user=current_user).order_by(Category.name).all(),
            'from_date': datetime_now.replace(day=1).strftime('%d-%m-%Y'),
            'to_date': datetime_now.replace(day=end_month_day).strftime('%d-%m-%Y')}

    return render_template('dashboard/home.html', data=data)


@dashboard_blueprint.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('dashboard/settings.html')
