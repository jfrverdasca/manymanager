import math

from flask import Blueprint, current_app, request
from flask_login import current_user
from flask_restful import Resource, reqparse, marshal_with, fields, abort
from sqlalchemy import String
from sqlalchemy.sql import func, desc, cast, or_
from dateutil.relativedelta import relativedelta
from datetime import datetime
from calendar import month_name
from dashboard import api
from dashboard.models import db, Category, Expense
from dashboard.utilities import get_expenses_by_date_interval_category

api_blueprint = Blueprint('api', __name__)


# general fields
expense_fields = {
    'description': fields.String,
    'timestamp': fields.DateTime,
    'value': fields.Float,
    'is_favorite': fields.Boolean,
    'favorite_order': fields.Integer
}

# tables
datatables_draw_values = {'expensesTable': 1,
                          'categoriesBalanceTable': 1,
                          'categoriesTable': 1,
                          'favoritesTable': 1}


class ExpensesTable(Resource):

    # keep these variables with the same values as in Datatables javascript code
    TABLE_NAME = 'expensesTable'
    PAGE_LENGTH = 25
    COLUMNS_INDEX = {
        0: (Expense.description, str),
        1: (Expense.category, Category),
        2: (Expense.timestamp, datetime),  # default order column
        3: (Expense.value, float),
        4: ('Options', None)}

    def get(self, from_date: datetime, to_date: datetime, category_id: int):
        ordered_column, _ = self.COLUMNS_INDEX[request.args.get('order[0][column]', 2, int)]
        order_direction = request.args.get('order[0][dir]', 'desc')
        item_index_start = request.args.get('start', 0, int)
        page_length = request.args.get('length', self.PAGE_LENGTH, int)
        search_value = request.args.get('search[value]', '')

        # add hour information to date
        from_date = from_date.replace(hour=0, minute=0, second=0)
        to_date = to_date.replace(hour=23, minute=59, second=59)

        # search
        search_parameters = list()
        if search_value:
            for index in self.COLUMNS_INDEX:
                # is searchable
                if request.args.get(f'columns[{index}][searchable]', False):
                    column, data_type = self.COLUMNS_INDEX[index]
                    if column is Expense.category:  # expense category relationship
                        search_parameters.append(Category.name.contains(search_value))

                    elif type(search_value) != data_type:
                        search_parameters.append(cast(column, String).contains(search_value))

                    else:
                        search_parameters.append(column.contains(search_value))

        # get records from database
        if category_id:
            expense_records = Expense.query.filter(Expense.user == current_user,
                                                   Expense.timestamp >= from_date,
                                                   Expense.timestamp <= to_date,
                                                   Expense.category_id == category_id,
                                                   Expense.accepted,
                                                   or_(*search_parameters))

        else:
            expense_records = Expense.query.filter(Expense.user == current_user,
                                                   Expense.timestamp >= from_date,
                                                   Expense.timestamp <= to_date,
                                                   Expense.accepted,
                                                   or_(*search_parameters)) \
                .join(Category, Expense.category_id == Category.id)

        # order
        if order_direction == 'desc':
            # expense category relationship
            expense_records = expense_records.order_by(desc(Category.name)) \
                if ordered_column is Expense.category else expense_records.order_by(desc(ordered_column))

        else:
            # expense category relationship
            expense_records = expense_records.order_by(Category.name) \
                if ordered_column is Expense.category else expense_records.order_by(ordered_column)

        records_count = expense_records.count()
        if page_length < 0:  # user wants to see all records
            page_length = records_count

        rows = list()
        if records_count > 0:
            # pagination
            paginate = expense_records.paginate(
                (item_index_start + page_length) / page_length,
                per_page=page_length)

            for item in paginate.items:
                rows.append([item.description,
                             {'name': item.category.name,
                              'color': item.category.color},
                             item.timestamp.strftime(current_app.config.get('DATETIME_FORMAT')),
                             item.value,
                             item.id])

        response = {'draw': datatables_draw_values[self.TABLE_NAME],
                    'recordsTotal': records_count,
                    'recordsFiltered': records_count,
                    'data': rows}

        datatables_draw_values[self.TABLE_NAME] += 1

        return response


api.add_resource(ExpensesTable, '/expenses_table/<date:from_date>/<date:to_date>/<int:category_id>/')


class CategoriesBalanceTable(Resource):

    # keep these variables with the same values as in Datatables javascript code
    TABLE_NAME = 'categoriesBalanceTable'
    PAGE_LENGTH = 5
    COLUMNS_INDEX = {
        0: (Category.name, str),
        1: ('Limit', float),
        2: ('Balance', float),
        3: ('Spent', float)}

    def get(self, from_date: datetime, to_date: datetime, category_id: int):
        ordered_column = request.args.get('order[0][column]', 3, int)  # order done with python (not SQL)
        order_direction = request.args.get('order[0][dir]', 'desc')
        item_index_start = request.args.get('start', 0, int)
        page_length = request.args.get('length', self.PAGE_LENGTH, int)
        search_value = request.args.get('search[value]', '')

        # add hour information to date
        from_date = from_date.replace(hour=0, minute=0, second=0)
        to_date = to_date.replace(hour=23, minute=59, second=59)

        # calculate the number of months between from date and to date
        months_between_dates = ((to_date.year - from_date.year) * 12 + to_date.month - from_date.month) + 1

        # get records from database
        expense_records = get_expenses_by_date_interval_category(current_user, from_date, to_date, category_id)

        # get expense sum by category
        expenses_sum_by_category = expense_records \
            .join(Category, Expense.category_id == Category.id) \
            .with_entities(Category, func.sum(Expense.value).label('sum')) \
            .group_by(Category.id) \
            .order_by(Category.name)

        records_count = expenses_sum_by_category.count()
        if page_length < 0:  # user wants to see all records
            page_length = records_count

        rows = list()
        if records_count > 0:
            # pagination
            paginate = expenses_sum_by_category.paginate(
                (item_index_start + page_length) / page_length,
                per_page=page_length)

            for category, expenses_sum in paginate.items:
                months_category_limit = category.limit * months_between_dates

                row_data = [
                    {'name': category.name,
                     'color': category.color},
                    months_category_limit,
                    round(months_category_limit - expenses_sum, 2),
                    round(expenses_sum, 2)]

                # search
                if search_value:
                    if any(map(lambda v: search_value in (v['name'] if isinstance(v, dict) else str(v)), row_data)):
                        rows.append(row_data)

                else:
                    rows.append(row_data)

            # order
            if order_direction == 'desc':
                rows.sort(key=lambda i: i[ordered_column]) \
                    if ordered_column > 0 else rows.sort(key=lambda i: i[ordered_column]['name'])

            else:
                rows.sort(key=lambda i: i[ordered_column], reverse=True) \
                    if ordered_column > 0 else rows.sort(key=lambda i: i[ordered_column]['name'], reverse=True)

        response = {'draw': datatables_draw_values[self.TABLE_NAME],
                    'recordsTotal': records_count,
                    'recordsFiltered': records_count,
                    'data': rows}

        datatables_draw_values[self.TABLE_NAME] += 1

        return response


api.add_resource(CategoriesBalanceTable, '/categories_balance_table/<date:from_date>/<date:to_date>/<int:category_id>/')


class SettingsCategoriesTable(Resource):

    # keep these variables with the same values as in Datatables javascript code
    TABLE_NAME = 'categoriesTable'
    PAGE_LENGTH = 10
    COLUMNS_INDEX = {
        0: (Category.name, str),
        1: (Category.limit, float),
        2: ('Options', None)}

    def get(self):
        ordered_column, _ = self.COLUMNS_INDEX[request.args.get('order[0][column]', 0, int)]  # order done with python (not SQL)
        order_direction = request.args.get('order[0][dir]', 'desc')
        item_index_start = request.args.get('start', 0, int)
        page_length = request.args.get('length', self.PAGE_LENGTH, int)
        search_value = request.args.get('search[value]', '')

        # search
        search_parameters = list()
        if search_value:
            for index in self.COLUMNS_INDEX:
                # is searchable
                if request.args.get(f'columns[{index}][searchable]', False):
                    column, data_type = self.COLUMNS_INDEX[index]
                    if type(search_value) != data_type:
                        search_parameters.append(cast(column, String).contains(search_value))

                    else:
                        search_parameters.append(column.contains(search_value))

        # get records from database
        category_records = Category.query.filter(Category.user == current_user,
                                                 or_(*search_parameters))

        # order
        category_records = category_records.order_by(desc(ordered_column)) \
            if order_direction == 'desc' else category_records.order_by(ordered_column)

        records_count = category_records.count()
        if page_length < 0:
            page_length = records_count

        rows = list()
        if records_count > 0:
            # pagination
            paginate = category_records.paginate(
                (item_index_start + page_length) / page_length,
                per_page=page_length)

            for item in paginate.items:
                rows.append([{'name': item.name,
                              'color': item.color},
                             item.limit,
                             item.id])

        response = {'draw': datatables_draw_values[self.TABLE_NAME],
                    'recordsTotal': records_count,
                    'recordsFiltered': records_count,
                    'data': rows}

        datatables_draw_values[self.TABLE_NAME] += 1

        return response


api.add_resource(SettingsCategoriesTable, '/categories_table/')


class SettingsFavoritesTable(Resource):

    # keep these variables with the same values as in Datatables javascript code
    TABLE_NAME = 'favoritesTable'
    PAGE_LENGTH = 10
    COLUMNS_INDEX = {
        0: (Expense.description, str),
        1: (Expense.value, float),
        2: ('Options', None),
        3: (Expense.favorite_sort, int)}

    def get(self):
        ordered_column, _ = self.COLUMNS_INDEX[request.args.get('order[0][column]', -1, int)]
        order_direction = request.args.get('order[0][dir]', 'desc')
        item_index_start = request.args.get('start', 0, int)
        page_length = request.args.get('length', self.PAGE_LENGTH, int)
        search_value = request.args.get('search[value]', '')

        # search
        search_parameters = list()
        if search_value:
            for index in self.COLUMNS_INDEX:
                # is searchable
                if request.args.get(f'columns[{index}][searchable]', False):
                    column, data_type = self.COLUMNS_INDEX[index]
                    if type(search_value) != data_type:
                        search_parameters.append(cast(column, String).contains(search_value))

                    else:
                        search_parameters.append(column.contains(search_value))

        # get records from database
        favorite_records = Expense.query.filter(Expense.user == current_user,
                                                Expense.is_favorite,
                                                Expense.accepted,
                                                or_(*search_parameters)) \
            .join(Category, Expense.category_id == Category.id)

        # order
        if order_direction == 'desc':
            favorite_records = favorite_records.order_by(desc(ordered_column))

        else:
            favorite_records = favorite_records.order_by(ordered_column)

        records_count = favorite_records.count()
        if page_length < 0:
            page_length = records_count

        rows = list()
        if records_count > 0:
            # pagination
            paginate = favorite_records.paginate(
                (item_index_start + page_length) / page_length,
                per_page=page_length)

            for item in paginate.items:
                rows.append([{'name': item.description,
                              'color': item.category.color},
                             item.value,
                             item.id,
                             item.favorite_sort])

        response = {'draw': datatables_draw_values[self.TABLE_NAME],
                    'recordsTotal': records_count,
                    'recordsFiltered': records_count,
                    'data': rows}

        datatables_draw_values[self.TABLE_NAME] += 1

        return response


api.add_resource(SettingsFavoritesTable, '/favorites_table/')

# charts
class ExpensesCategoriesChart(Resource):

    def get(self, from_date, to_date, category_id):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        to_date = to_date.replace(hour=23, minute=59, second=59)

        if category_id:
            expenses = get_expenses_by_date_interval_category(current_user, from_date, to_date, category_id)

        else:
            expenses = get_expenses_by_date_interval_category(current_user, from_date, to_date)

        expenses_sum_by_category = expenses \
            .join(Category, Expense.category_id == Category.id) \
            .with_entities(Category, func.sum(Expense.value).label('sum')) \
            .group_by(Category) \
            .order_by(desc('sum'))

        labels = list()
        datasets = {'data': list(),
                    'backgroundColor': list(),
                    'borderWidth': 1}
        for category, expenses_sum in expenses_sum_by_category:
            labels.append(category.name)

            datasets['data'].append(round(expenses_sum, 2))
            datasets['backgroundColor'].append(category.color)

        response = {'chart_data': {'labels': labels,
                                   'datasets': [datasets]},
                    'total': round(sum(datasets['data']), 2)}

        return response


api.add_resource(ExpensesCategoriesChart, '/spent-by-category-chart/<date:from_date>/<date:to_date>/<int:category_id>')


class QuickHistoryChart(Resource):

    def get(self, months):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        to_date = datetime.now()
        from_date = to_date - relativedelta(months=months)

        month_trunc = func.date_trunc('month', Expense.timestamp)
        expenses = Expense.query.filter(Expense.user == current_user,
                                        Expense.timestamp >= from_date,
                                        Expense.timestamp <= to_date) \
            .join(Category, Expense.category_id == Category.id) \
            .with_entities(Category, func.sum(Expense.value).label('sum'), month_trunc) \
            .group_by(month_trunc, Category) \
            .order_by(month_trunc)

        datasets = {c.name: {'label': c.name,
                             'data': [0 for _ in range(months)],
                             'borderColor': c.color,
                             'backgroundColor': c.color,
                             'fill': False} for c in expenses.with_entities(Category)}

        for category, sum, date in expenses:
            month_list_index = abs(((date.year - from_date.year) * 12) + (date.month - from_date.month - 1))
            datasets[category.name]['data'][month_list_index] = sum

        return {'labels': list(map(lambda m: month_name[(m % 12) + 1],
                                   range(from_date.month, from_date.month + months))),
                'datasets': list(datasets.values())}


api.add_resource(QuickHistoryChart, '/quick-history-chart/<int:months>')


# favorites
class Favorite(Resource):

    favorite_args = reqparse.RequestParser()
    favorite_args.add_argument('is_favorite', type=bool)
    favorite_args.add_argument('sort', type=int)

    @marshal_with(expense_fields)
    def patch(self, favorite_id):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        expense = Expense.query.filter_by(user=current_user, id=favorite_id, is_favorite=True).first()
        if not expense:
            abort(404, message=f'Favorite with id {favorite_id} not found')

        request_args = self.favorite_args.parse_args()
        is_favorite = request_args.get('is_favorite')
        sort = request_args.get('sort')

        if is_favorite is not None:
            expense.is_favorite = is_favorite

        try:
            expense.set_favorite_sort(sort)
            db.session.commit()

        except Exception as e:
            abort(500, message=str(e))

        return expense


api.add_resource(Favorite, '/favorite/<int:favorite_id>')


class FavoriteReplica(Resource):

    replica_args = reqparse.RequestParser()
    replica_args.add_argument('id', type=int, required=True, help='id is required')

    @marshal_with(expense_fields)
    def post(self):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        request_args = self.replica_args.parse_args()
        favorite_id = request_args.get('id')

        expense = Expense.query.filter_by(user=current_user, id=favorite_id, is_favorite=True).first()
        if not expense:
            abort(404, message=f'Favorite with id {favorite_id} not found')

        try:
            replica = Expense(description=expense.description,
                              value=expense.value,
                              user=current_user,
                              category_id=expense.category_id)

            db.session.add(replica)
            db.session.commit()

        except Exception as e:
            abort(500, message=str(e))

        else:
            return replica


api.add_resource(FavoriteReplica, '/favorite-replica')
