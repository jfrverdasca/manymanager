from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime
from calendar import monthrange
from dashboard.models import Category

dashboard_blueprint = Blueprint('dashboard', __name__)


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
