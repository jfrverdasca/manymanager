from flask import Blueprint, render_template, redirect, abort, url_for, flash, Response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from datetime import datetime
from calendar import monthrange
from dashboard.models import db, User, Expense, Category
from dashboard.utilities import send_email
from .forms import ExpenseForm, CategoryForm, DeleteForm

dashboard_blueprint = Blueprint('dashboard', __name__)


# ajax
@dashboard_blueprint.route('/expenses-categories-balance-tables/<date:from_date>/<date:to_date>/<int:category_id>',
                           methods=['GET'])
def expenses_categories_balance_tables(from_date, to_date, category_id):
    if not current_user.is_authenticated:
        abort(401)

    # add hour information to to date
    to_date = to_date.replace(hour=23, minute=59, second=59)

    months_between_dates = ((to_date.year - from_date.year) * 12 + to_date.month - from_date.month) + 1

    if category_id:
        expenses = Expense.query.filter(Expense.user == current_user,
                                        Expense.timestamp >= from_date,
                                        Expense.timestamp <= to_date,
                                        Expense.category_id == category_id,
                                        Expense.accepted)

    else:
        expenses = Expense.query.filter(Expense.user == current_user,
                                        Expense.timestamp >= from_date,
                                        Expense.timestamp <= to_date,
                                        Expense.accepted)

    data = {'expenses': expenses,
            'categories': list()}

    expenses_sum_by_category = expenses \
        .join(Category, Expense.category_id == Category.id) \
        .with_entities(Category, func.sum(Expense.value).label('sum')) \
        .group_by(Category.id)
    for category, expenses_sum in expenses_sum_by_category:
        months_category_limit = category.limit * months_between_dates

        data['categories'].append({'category': category,
                                   'limit': months_category_limit,
                                   'balance': round(months_category_limit - expenses_sum, 2),
                                   'spent': round(expenses_sum, 2)})

    return render_template('dashboard/ajax/expenses_categories_balance_tables.html', data=data)


@dashboard_blueprint.route('/favorites-list', methods=['GET'])
def favorites_list():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/favorites_list.html',
                           favorites=Expense.query.filter_by(user=current_user, accepted=True, is_favorite=True)
                           .join(Category, Expense.category_id == Category.id)
                           .order_by(Expense.favorite_sort)
                           .all())


@dashboard_blueprint.route('/categories_favorites_tables', methods=['GET'])
def categories_favorites_tables():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/categories_favorites_tables.html', data={
        'categories': Category.query.filter_by(user=current_user),
        'favorites': Expense.query.filter_by(user=current_user, is_favorite=True)})


# popups
@dashboard_blueprint.route('/expense/new', methods=['GET', 'POST'])
def expense_create_form():
    if not current_user.is_authenticated:
        abort(401)

    form = ExpenseForm()
    form.category.choices = Category.query.filter_by(user=current_user).order_by('name').all()
    if form.validate_on_submit():
        try:
            expense = Expense(description=form.description.data,
                              timestamp=datetime.fromisoformat(f'{form.date.data}T{form.time.data}'),
                              value=form.value.data,
                              is_favorite=form.is_favorite.data,
                              user=current_user,
                              category_id=form.category.data)

            db.session.add(expense)
            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.date.data = datetime.now().date()
    form.time.data = datetime.now().time()

    return render_template('dashboard/forms/expense_form.html', form=form)


@dashboard_blueprint.route('/expense/<int:expense_id>/update', methods=['GET', 'POST'])
def expense_update_form(expense_id):
    if not current_user.is_authenticated:
        abort(401)

    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(401)

    form = ExpenseForm(obj=expense)
    form.category.choices = Category.query.filter_by(user=current_user).order_by('name').all()
    if form.validate_on_submit():
        try:
            expense.description = form.description.data
            expense.timestamp = datetime.fromisoformat(f'{form.date.data}T{form.time.data}')
            expense.value = form.value.data
            expense.is_favorite = form.is_favorite.data
            expense.category_id = form.category.data

            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.date.data = expense.timestamp.date()
    form.time.data = expense.timestamp.time()

    return render_template('dashboard/forms/expense_form.html', form=form)


@dashboard_blueprint.route('/expense/<int:expense_id>/delete', methods=['GET', 'POST'])
def expense_delete_form(expense_id):
    if not current_user.is_authenticated:
        abort(401)

    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            db.session.delete(expense)
            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/expense_delete_form.html', form=form, object=expense)


@dashboard_blueprint.route('/category/new', methods=['GET', 'POST'])
def category_create_form():
    if not current_user.is_authenticated:
        abort(401)

    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = Category(name=form.name.data,
                                limit=form.limit.data,
                                color=form.color.data,
                                user=current_user)

            db.session.add(category)
            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_form.html', form=form)


@dashboard_blueprint.route('/category/<int:category_id>/update', methods=['GET', 'POST'])
def category_update_form(category_id):
    if not current_user.is_authenticated:
        abort(401)

    category = Category.query.get_or_404(category_id)
    if category.user != current_user:
        abort(401)

    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.limit = form.limit.data
            category.color = form.color.data

            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_form.html', form=form)


@dashboard_blueprint.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def category_delete_form(category_id):
    if not current_user.is_authenticated:
        abort(401)

    category = Category.query.get_or_404(category_id)
    if category.user != current_user:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            db.session.delete(category)
            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_delete_form.html', form=form, object=category)


@dashboard_blueprint.route('/favorite/<int:expense_id>/remove', methods=['GET', 'POST'])
def favorite_remove_form(expense_id):
    if not current_user.is_authenticated:
        abort(401)

    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            expense.is_favorite = False

            db.session.commit()

        except Exception as e:
            abort(500, e)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/favorite_remove_form.html', form=form, object=expense)


# TODO: rever
@dashboard_blueprint.route('/share/new', methods=['GET', 'POST'])
def share_form_create():
    if not current_user.is_authenticated:
        abort(401)

    # form = ShareForm()
    # if form.validate_on_submit():
    #     try:
    #         user = User.query.filter_by(email=form.email.data).first()
    #         if not user:
    #             return Response(status=200)
    #
    #         share = Share.query.filter_by(owner=current_user.id, user=user.id, active=False).first()
    #         if share:
    #             share.active = True
    #             share.request_timestamp = datetime.now()
    #
    #             db.session.commit()
    #
    #         else:
    #             share = Share(owner=current_user.id, user=user.id)
    #
    #             db.session.add(share)
    #             db.session.commit()
    #
    #         send_email(user.email, 'ManyManager: Share invitation',
    #                    f'''You have been invited by {current_user.email} to share expenses.
    #                    To accept the invitation please visit the following link:
    #                    {url_for('dashboard.share_activate', token=share.get_share_token(), _external=True)}
    #                    If you did not recognize this request, please ignore this message''')
    #
    #     except Exception:
    #         abort(500)
    #
    #     else:
    #         return Response(status=200)

    return render_template('dashboard/forms/share_form.html', form=form)


# TODO: rever
@dashboard_blueprint.route('/share-activate/<token>', methods=['GET', 'POST'])
def share_activate(token):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))



    # share = Share.check_share_token(token)
    # if not share:
    #     flash('Invalid or expired share token', 'danger')
    #     return redirect(url_for('dashboard.settings'))
    #
    # else:
    #     share.active = True
    #
    #     db.session.commit()
    #
    # flash(f'You can now share expenses with {share.owner}', 'success')
    return redirect(url_for('dashboard.settings'))


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
