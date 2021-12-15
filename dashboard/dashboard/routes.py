from flask import Blueprint, render_template, abort, Response
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from datetime import datetime
from calendar import monthrange
from dashboard.models import db, Expense, Category
from .forms import ExpenseForm, CategoryForm, DeleteForm

dashboard_blueprint = Blueprint('dashboard', __name__)


# ajax
@dashboard_blueprint.route('/home-tables/<date:from_date>/<date:to_date>/<int:category_id>', methods=['GET'])
def home_tables(from_date, to_date, category_id):
    if not current_user.is_authenticated:
        abort(401)

    expenses = None
    categories = Category.query.filter_by(owner=current_user.id)
    if category_id:
        temporary_category = categories.filter_by(id=category_id).first()
        if temporary_category:
            categories = temporary_category
            expenses = Expense.query.filter(Expense.owner == current_user.id,
                                            Expense.timestamp >= from_date,
                                            Expense.timestamp <= to_date,
                                            Expense.category_id == categories.id)

    if not expenses:
        expenses = Expense.query.filter(Expense.owner == current_user.id,
                                        Expense.timestamp >= from_date,
                                        Expense.timestamp <= to_date)

    data = {'expenses': expenses.all(),
            'categories': list()}

    expenses_categories_sum = expenses\
        .with_entities(Expense.category_id, func.sum(Expense.value).label('sum'))\
        .group_by(Expense.category_id)
    for category_id, category_sum in expenses_categories_sum:
        if isinstance(categories, Category):
            category = categories

        else:
            category = categories.filter_by(id=category_id).first()

        data['categories'].append({'category_obj': category,
                                   'balance': round(category.limit - category_sum, 2),
                                   'spent': round(category_sum, 2)})

    return render_template('dashboard/ajax/home_tables.html', data=data)


@dashboard_blueprint.route('/favorites', methods=['GET'])
def favorites():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/home_favorites.html',
                           favorites=Expense.query.filter_by(owner=current_user.id, is_favorite=True)
                           .join(Category, Expense.category_id == Category.id).order_by('favorite_order').all())


@dashboard_blueprint.route('/settings-table', methods=['GET'])
def settings_table():
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard/ajax/settings_tables.html', data={
        'categories': Category.query.filter_by(owner=current_user.id).all(),
        'favorites': Expense.query.filter_by(owner=current_user.id, is_favorite=True).all()})


# popups
@dashboard_blueprint.route('/expense/new', methods=['GET', 'POST'])
def expense_form_create():
    if not current_user.is_authenticated:
        abort(401)

    form = ExpenseForm()
    form.category.choices = Category.query.filter_by(owner=current_user.id).order_by('name').all()
    if form.validate_on_submit():
        try:
            expense = Expense(description=form.description.data,
                              timestamp=datetime.fromisoformat(f'{form.date.data}T{form.time.data}'),
                              value=form.value.data,
                              is_favorite=form.is_favorite.data,
                              owner=current_user.id,
                              category_id=form.category.data)

            db.session.add(expense)
            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.date.data = datetime.now().date()
    form.time.data = datetime.now().time()

    return render_template('dashboard/forms/expense_form.html', form=form)


@dashboard_blueprint.route('/expense/<int:expense_id>/update', methods=['GET', 'POST'])
def expense_form_update(expense_id):
    if not current_user.is_authenticated:
        abort(401)

    expense = Expense.query.get_or_404(expense_id)
    if expense.owner != current_user.id:
        abort(401)

    form = ExpenseForm()
    form.category.choices = Category.query.filter_by(owner=current_user.id).order_by('name').all()
    if form.validate_on_submit():
        try:
            expense.description = form.description.data
            expense.timestamp = datetime.fromisoformat(f'{form.date.data}T{form.time.data}')
            expense.value = form.value.data
            expense.is_favorite = form.is_favorite.data
            expense.category_id = form.category.data

            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.description.data = expense.description
    form.date.data = expense.timestamp.date()
    form.time.data = expense.timestamp.time()
    form.value.data = expense.value
    form.is_favorite.data = expense.is_favorite
    form.category.data = expense.category_id

    return render_template('dashboard/forms/expense_form.html', form=form)


@dashboard_blueprint.route('/expense/<int:expense_id>/delete', methods=['GET', 'POST'])
def expense_form_delete(expense_id):
    if not current_user.is_authenticated:
        abort(403)

    expense = Expense.query.get_or_404(expense_id)
    if expense.owner != current_user.id:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            db.session.delete(expense)
            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/expense_delete_form.html', form=form, object=expense)


@dashboard_blueprint.route('/category/new', methods=['GET', 'POST'])
def category_form_create():
    if not current_user.is_authenticated:
        abort(401)

    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = Category(name=form.name.data,
                                description=form.description.data,
                                limit=form.limit.data,
                                color=form.color.data,
                                owner=current_user.id)

            db.session.add(category)
            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_form.html', form=form)


@dashboard_blueprint.route('/category/<int:category_id>/update', methods=['GET', 'POST'])
def category_form_update(category_id):
    if not current_user.is_authenticated:
        abort(403)

    category = Category.query.get_or_404(category_id)
    if category.owner != current_user.id:
        abort(401)

    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            category.description = form.description.data
            category.limit = form.limit.data
            category.color = form.color.data

            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.name.data = category.name
    form.description.data = category.description
    form.limit.data = category.limit
    form.color.data = category.color

    return render_template('dashboard/forms/category_form.html', form=form)


@dashboard_blueprint.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def category_form_delete(category_id):
    if not current_user.is_authenticated:
        abort(403)

    category = Category.query.get_or_404(category_id)
    if category.owner != current_user.id:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            db.session.delete(category)
            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_delete_form.html', form=form, object=category)


@dashboard_blueprint.route('/favorite/<int:expense_id>/remove', methods=['GET', 'POST'])
def favorite_form_remove(expense_id):
    if not current_user.is_authenticated:
        abort(403)

    expense = Expense.query.get_or_404(expense_id)
    if expense.owner != current_user.id:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            expense.is_favorite = False

            db.session.commit()

        except Exception:
            abort(500)

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/remove_favorite_form.html', form=form, object=expense)


# pages
@dashboard_blueprint.route('/', methods=['GET'])
@dashboard_blueprint.route('/index', methods=['GET'])
@dashboard_blueprint.route('/home', methods=['GET'])
@login_required
def home():
    datetime_now = datetime.now()
    _, end_month_day = monthrange(datetime_now.year, datetime_now.month)

    data = {'categories': Category.query.filter_by(owner=current_user.id).order_by(Category.name).all(),
            'from_date': datetime_now.replace(day=1).strftime('%d-%m-%Y'),
            'to_date': datetime_now.replace(day=end_month_day).strftime('%d-%m-%Y')}

    return render_template('dashboard/home.html', data=data)


@dashboard_blueprint.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('dashboard/settings.html')
