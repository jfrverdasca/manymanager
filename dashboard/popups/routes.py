from flask import Blueprint, render_template, url_for, abort, Response
from flask_login import current_user
from sqlalchemy.sql import and_
from sqlalchemy.orm import aliased
from datetime import datetime
from dashboard.utilities import send_email
from dashboard.decorators import login_required_401
from dashboard.models import db, User, Expense, Category, Share, Alert
from .forms import ExpenseForm, CategoryForm, DeleteForm, ShareRequestForm

popups_blueprint = Blueprint('popup', __name__)


# popups
@login_required_401
@popups_blueprint.route('/expense/new', methods=['GET', 'POST'])
def expense_create_form():
    shares = Share.query.filter_by(shared_by=current_user)

    form = ExpenseForm(shares=shares)
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

            # handle shared expenses
            has_uncommitted_changes = False
            for share in form.shares:
                if share.value.data == 0:
                    continue

                shared_expense = expense.create_shared_expense(share.user.data, share.value.data)
                db.session.add(shared_expense)

                # create the shared expense alert
                db.session.add(Alert.shared_expense_alert(current_user, shared_expense))

                has_uncommitted_changes = True

            if has_uncommitted_changes:
                db.session.commit()

        except Exception as e:
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.date.data = datetime.now().date()
    form.time.data = datetime.now().time()

    return render_template('dashboard/forms/expense_form.html', form=form)


@login_required_401
@popups_blueprint.route('/expense/<int:expense_id>/update', methods=['GET', 'POST'])
def expense_update_form(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(401)

    user_alias = aliased(User, name='user')  # force the name "user" in the resulting named tuple of with_entities
    shares = Share.query.outerjoin(Expense, and_(Share.right_id == Expense.user_id, Expense.parent_id == expense.id)) \
        .join(user_alias, Share.right_id == User.id) \
        .filter(Share.left_id == current_user.id) \
        .with_entities(user_alias, Expense.value).all()

    has_parent = True if expense.parent_id else False

    form = ExpenseForm(obj=expense, has_parent=has_parent, shares=shares)
    form.category.choices = Category.query.filter_by(user=current_user).order_by('name').all()
    if form.validate_on_submit():
        try:
            expense.description = form.description.data
            expense.timestamp = datetime.fromisoformat(f'{form.date.data}T{form.time.data}')
            expense.is_favorite = form.is_favorite.data
            expense.category_id = form.category.data

            # set alert as seen
            if expense.alerts:
                for unseen_alert in filter(lambda a: not a.seen, expense.alerts):
                    unseen_alert.seen = True

            # only allow to change the value of an expense if not shared by other user
            if not has_parent:
                expense.value = form.value.data

            db.session.commit()

            # handle shared expenses
            has_uncommitted_changes = False
            for share in form.shares:
                shared_expense = Expense.query.filter_by(user_id=share.user.data, parent_id=expense.id).first()

                # user can edit an expense and add/remove users to that existing expense
                share_value = share.value.data
                if not shared_expense:
                    if share_value in [None, 0]:
                        continue

                    # used added a new share to the expense
                    shared_expense = expense.create_shared_expense(share.user.data, share.value.data)
                    db.session.add(shared_expense)

                    # create the shared expense alert
                    db.session.add(Alert.shared_expense_alert(current_user, shared_expense))

                # user removed a shared expense
                elif share_value in [None, 0]:
                    db.session.delete(shared_expense)

                    # create the shared expense delete alert
                    db.session.add(Alert.shared_expense_delete_alert(current_user, shared_expense))

                # user changed the value of a shared expense
                elif share_value != shared_expense.value:
                    shared_expense.value = share_value

                    # create the shared expense update alert
                    db.session.add(Alert.shared_expense_update_alert(current_user, shared_expense))

                else:
                    continue  # avoid changing the value of the flag has_uncommitted_changes

                has_uncommitted_changes = True

            if has_uncommitted_changes:
                db.session.commit()

        except Exception as e:
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    form.date.data = expense.timestamp.date()
    form.time.data = expense.timestamp.time()

    return render_template('dashboard/forms/expense_form.html', form=form)


@login_required_401
@popups_blueprint.route('/expense/<int:expense_id>/delete', methods=['GET', 'POST'])
def expense_delete_form(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(401)

    shares = Expense.query.join(Share, and_(Expense.user_id == Share.right_id, Expense.parent_id == expense.id)) \
        .filter(Share.left_id == current_user.id).all()

    form = DeleteForm(shares=shares)
    if form.validate_on_submit():
        try:
            # TODO: change delete method and generate alerts

            db.session.delete(expense)  # cascade will delete shared expenses also
            db.session.commit()

        except Exception as e:
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/expense_delete_form.html', form=form, object=expense)


@login_required_401
@popups_blueprint.route('/category/new', methods=['GET', 'POST'])
def category_create_form():
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
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_form.html', form=form)


@login_required_401
@popups_blueprint.route('/category/<int:category_id>/update', methods=['GET', 'POST'])
def category_update_form(category_id):
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
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_form.html', form=form)


@login_required_401
@popups_blueprint.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def category_delete_form(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user != current_user:
        abort(401)

    form = DeleteForm()
    if form.validate_on_submit():
        try:
            db.session.delete(category)
            db.session.commit()

        except Exception as e:
            return Response(status=500, response=str(e))

        else:
            return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/category_delete_form.html', form=form, object=category)


@login_required_401
@popups_blueprint.route('/favorite/<int:expense_id>/remove', methods=['GET', 'POST'])
def favorite_remove_form(expense_id):
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


@login_required_401
@popups_blueprint.route('/share_request_form', methods=['GET', 'POST'])
def share_request_form():
    form = ShareRequestForm()
    if form.validate_on_submit():
        try:
            share_with_user = User.query.filter_by(email=form.email.data).first()
            if share_with_user:
                send_email(share_with_user.email, 'ManyManager: Request sharing permission',
                           f'''User {current_user.username} is asking for permission to share expenses with you. 
                           To enable expense sharing visit the following link: 
                           {url_for('auth.share_with_user', token=current_user.get_share_with_token(), _external=True)}
                           If you did not make this request please ignore this message''')

        except Exception as e:
            print(e)
            # TODO: colocar a excepção em logs

        return Response(status=200)  # status 200 and no request data means success (close popup)

    return render_template('dashboard/forms/share_request_form.html', form=form)
