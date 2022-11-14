from flask import Blueprint, render_template, abort
from flask_login import current_user
from dashboard.decorators import login_required_401
from dashboard.models import Expense, Category, Alert

ajax_blueprint = Blueprint('ajax', __name__)


# ajax
@login_required_401
@ajax_blueprint.route('/favorites-list', methods=['GET'])
def favorites_list():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/favorites_list.html',
                           favorites=Expense.query.filter_by(user=current_user, is_favorite=True)
                           .join(Category, Expense.category_id == Category.id)
                           .order_by(Expense.favorite_sort)
                           .all())


@login_required_401
@ajax_blueprint.route('/alerts-list', methods=['GET'])
def alerts_list():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/alerts_list.html',
                           alerts=Alert.query.filter_by(user=current_user, seen=False).all())
