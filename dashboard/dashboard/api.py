from flask import Blueprint
from flask_login import current_user
from flask_restful import Resource, reqparse, marshal_with, marshal, fields, abort
from sqlalchemy.sql import func, desc
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

        expenses = None
        if category_id:
            category = Category.query.filter_by(id=category_id, owner=current_user.id).first()
            if category:
                expenses = \
                    Expense.query.filter(Expense.owner == current_user.id,
                                         Expense.timestamp >= from_date,
                                         Expense.timestamp <= to_date,
                                         Expense.category_id == category.id)\
                    .join(Category, Expense.category_id == Category.id) \
                    .with_entities(Category, func.sum(Expense.value).label('sum')) \
                    .group_by(Category) \
                    .order_by(desc('sum'))

        if not expenses:
            expenses = \
                Expense.query.filter(Expense.timestamp >= from_date, Expense.timestamp <= to_date)\
                .join(Category, Expense.category_id == Category.id)\
                .with_entities(Category, func.sum(Expense.value).label('sum')) \
                .group_by(Category)\
                .order_by(desc('sum'))

        response = {'labels': list(),
                    'values': list(),
                    'colors': list()}
        for category_obj, category_sum in expenses:
            response['labels'].append(category_obj.name)
            response['values'].append(round(category_sum, 2))
            response['colors'].append(category_obj.color)

        response['total'] = round(sum(response['values']), 2)

        return response


api.add_resource(ExpensesCategoriesChart, '/expense-categories-chart/<date:from_date>/<date:to_date>/<int:category_id>')


class Favorite(Resource):

    favorite_args = reqparse.RequestParser()
    favorite_args.add_argument('is_favorite', type=bool)
    favorite_args.add_argument('order', type=int)

    @marshal_with(expense_fields)
    def patch(self, favorite_id):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        expense = Expense.query.filter_by(owner=current_user.id, id=favorite_id, is_favorite=True).first()
        if not expense:
            abort(404, message=f'Favorite with id {favorite_id} not found')

        request_args = self.favorite_args.parse_args()
        is_favorite = request_args.get('is_favorite')
        order = request_args.get('order')

        if is_favorite is not None:
            expense.is_favorite = is_favorite

        try:
            expense.set_favorite_order(order)
            db.session.commit()

        except Exception:
            abort(500)

        return expense


api.add_resource(Favorite, '/favorite/<int:favorite_id>')


class ExpenseReplica(Resource):

    replica_args = reqparse.RequestParser()
    replica_args.add_argument('id', type=int, required=True, help='Id is required')

    @marshal_with(expense_fields)
    def post(self):
        if not current_user.is_authenticated:
            abort(401, message='Authentication required')

        request_args = self.replica_args.parse_args()
        favorite_id = request_args.get('id')

        expense = Expense.query.filter_by(owner=current_user.id, id=favorite_id, is_favorite=True).first()
        if not expense:
            abort(404, message=f'Favorite with id {favorite_id} not found')

        try:
            expense_replica = Expense(description=expense.description,
                                      value=expense.value,
                                      owner=current_user.id,
                                      category_id=expense.category_id)

            db.session.add(expense_replica)
            db.session.commit()

        except Exception:
            abort(500)

        else:
            return expense_replica


api.add_resource(ExpenseReplica, '/expense-replica')
