import dashboard.rest.datatables as datatables

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


class ExpensesTable(Resource, datatables.DatatableHandler):

    # keep these variables with the same values as in Datatables javascript code
    COLUMNS_INDEX = {
        0: (Expense.description, str),
        1: (Category.name, str),
        2: (Expense.timestamp, datetime),  # default order column
        3: (Expense.value, float),
        4: ('Options', None)}

    @datatables.datatable_parser()
    def get(self, from_date: datetime, to_date: datetime, category_id: int):
        # get records from database
        expense_records = get_expenses_by_date_interval_category(current_user, from_date, to_date, category_id)

        # process datatables items
        items, total_items = self.handle_datatable_request(expense_records, self.COLUMNS_INDEX)

        rows = list()
        for item in items:
            rows.append({'description': item.description,
                         'category': {'name': item.category.name,
                                      'color': item.category.color},
                         'timestamp': item.timestamp.strftime(current_app.config.get('DATETIME_FORMAT')),
                         'value': item.value,
                         'id': item.id})

        return {'draw': self.datatable.draw,
                'recordsTotal': total_items,
                'recordsFiltered': total_items,
                'data': rows}


api.add_resource(ExpensesTable, '/expenses_table/<date:from_date>/<date:to_date>/<int:category_id>/')


class CategoriesBalanceTable(Resource, datatables.DatatableHandler):

    # keep these variables with the same values as in Datatables javascript code
    COLUMNS_INDEX = {
        0: (Category.name, str),
        1: ('Limit', float),
        2: ('Balance', float),
        3: ('Spent', float)}

    @datatables.datatable_parser()
    def get(self, from_date: datetime, to_date: datetime, category_id: int):
        # add hour information to date
        from_date = from_date.replace(hour=0, minute=0, second=0)
        to_date = to_date.replace(hour=23, minute=59, second=59)

        # calculate the number of months between from date and to date
        months_between_dates = ((to_date.year - from_date.year) * 12 + to_date.month - from_date.month) + 1

        # get records from database
        expense_records = get_expenses_by_date_interval_category(current_user, from_date, to_date, category_id)

        # get expense sum by category
        expenses_sum_by_category = expense_records \
            .with_entities(Category, func.sum(Expense.value).label('sum')) \
            .group_by(Category.id) \
            .order_by(Category.name)

        records_count = expenses_sum_by_category.count()
        if self.datatable.page_length < 0:  # user wants to see all records
            self.datatable.page_length = records_count

        # pagination
        paginate = expenses_sum_by_category.paginate(self.datatable.pagination_page,
                                                     per_page=self.datatable.page_length)

        rows = list()
        for category, expenses_sum in paginate.items:
            months_category_limit = round(category.limit * months_between_dates, 2)

            row_data = [{'name': category.name,
                         'color': category.color},
                        months_category_limit,
                        round(months_category_limit - expenses_sum, 2),
                        round(expenses_sum, 2)]

            # search
            if self.datatable.search_value and \
                not any(map(lambda v: self.datatable.search_value in
                                      (v['name'] if isinstance(v, dict) else str(v)), row_data)):
                continue

            else:
                rows.append(row_data)

        # order
        reverse = self.datatable.order_direction == 'asc'
        if getattr(self.datatable, f'column_{self.datatable.ordered_column}_orderable'):
            rows.sort(key=lambda i: i[self.datatable.ordered_column], reverse=reverse) \
                if self.datatable.ordered_column > 0 else \
                rows.sort(key=lambda i: i[self.datatable.ordered_column]['name'], reverse=reverse)

        return {'draw': self.datatable.draw,
                'recordsTotal': records_count,
                'recordsFiltered': records_count,
                'data': rows}


api.add_resource(CategoriesBalanceTable, '/categories_balance_table/<date:from_date>/<date:to_date>/<int:category_id>/')


class SettingsCategoriesTable(Resource, datatables.DatatableHandler):

    # keep these variables with the same values as in Datatables javascript code
    COLUMNS_INDEX = {
        0: (Category.name, str),
        1: (Category.limit, float),
        2: ('Options', None)}

    @datatables.datatable_parser()
    def get(self):
        # get records from database
        category_records = Category.query.filter(Category.user == current_user)

        # process datatables items
        items, total_items = self.handle_datatable_request(category_records, self.COLUMNS_INDEX)

        rows = list()
        for item in items:
            rows.append([{'name': item.name,
                          'color': item.color},
                         item.limit,
                         item.id])

        return {'draw': self.datatable.draw,
                'recordsTotal': total_items,
                'recordsFiltered': total_items,
                'data': rows}


api.add_resource(SettingsCategoriesTable, '/categories_table/')


class SettingsFavoritesTable(Resource, datatables.DatatableHandler):

    # keep these variables with the same values as in Datatables javascript code
    COLUMNS_INDEX = {
        0: (Expense.description, str),
        1: (Expense.value, float),
        2: ('Options', None),
        3: (Expense.favorite_sort, int)}

    @datatables.datatable_parser()
    def get(self):
        # get records from database
        favorite_records = Expense.query.filter(Expense.user == current_user,
                                                Expense.is_favorite,
                                                Expense.accepted) \
            .join(Category, Expense.category_id == Category.id)

        # process datatables items
        items, total_items = self.handle_datatable_request(favorite_records, self.COLUMNS_INDEX)

        rows = list()
        for item in items:
            rows.append([{'name': item.description,
                          'color': item.category.color},
                         item.value,
                         item.id,
                         item.favorite_sort])

        return {'draw': self.datatable.draw,
                'recordsTotal': total_items,
                'recordsFiltered': total_items,
                'data': rows}


api.add_resource(SettingsFavoritesTable, '/favorites_table/')


# charts
class ExpensesCategoriesChart(Resource):

    def get(self, from_date, to_date, category_id):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        from_data = from_date.replace(hour=0, minute=0, second=0)
        to_date = to_date.replace(hour=23, minute=59, second=59)

        expenses = get_expenses_by_date_interval_category(current_user, from_date, to_date, category_id)

        expenses_sum_by_category = expenses \
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

        to_date = datetime.now().replace(hour=23, minute=59, second=59)
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
