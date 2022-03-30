from flask import Blueprint
from flask_login import current_user
from flask_restful import Resource, reqparse, marshal_with, fields, abort
from sqlalchemy.sql import func, desc
from dateutil.relativedelta import relativedelta
from datetime import datetime
from calendar import month_name
from dashboard import api
from dashboard.models import db, Category, Expense

api_blueprint = Blueprint('api', __name__)


# general fields
category_fields = {
    'name': fields.String,
    'description': fields.String,
    'limit': fields.Float,
    'color': fields.String,
}

expense_fields = {
    'description': fields.String,
    'timestamp': fields.DateTime,
    'value': fields.Float,
    'is_favorite': fields.Boolean,
    'favorite_order': fields.Integer
}


class ExpensesCategoriesChart(Resource):

    def get(self, from_date, to_date, category_id):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        to_date = to_date.replace(hour=23, minute=59, second=59)

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
