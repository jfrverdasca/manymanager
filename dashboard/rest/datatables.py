from flask import request
from sqlalchemy import String
from sqlalchemy.sql import desc, cast, or_

from functools import wraps
from types import SimpleNamespace


def datatable_parser(default_ordered_column=None, default_order_direction=None):
    def wrapper(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            page_length = request.args.get('length', 10, int)  # 10 default datatable page length according to docs
            item_index_start = request.args.get('start', 0, int)

            draw = request.args.get('draw', None, int)
            if draw:
                draw += 1

            # get some fixed attributes
            datatable_data = {
                'draw': draw,
                'ordered_column': request.args.get('order[0][column]', default_ordered_column, int),
                'order_direction': request.args.get('order[0][dir]', default_order_direction),
                'pagination_page': (item_index_start + page_length) / page_length if page_length > 0 else 1,
                'page_length': page_length,
                'item_start_index': item_index_start,
                'search_value': request.args.get('search[value]', '')
            }

            # get mutable attributes
            index = 0
            while True:
                try:
                    # searchable
                    datatable_data[f'column_{index}_searchable'] = \
                        True if request.args[f'columns[{index}][searchable]'] == 'true' else False

                    # orderable
                    datatable_data[f'column_{index}_orderable'] = \
                        True if request.args[f'columns[{index}][orderable]'] == 'true' else False

                except KeyError:
                    break

                index += 1

            self.datatable = SimpleNamespace(**datatable_data)

            return f(self, *args, **kwargs)
        return inner
    return wrapper


class DatatableHandler:

    datatable = None

    def handle_datatable_request(self, records, columns_index_type):
        ordered_column, _ = columns_index_type[self.datatable.ordered_column]

        # filter
        search_parameters = list()
        if self.datatable.search_value:
            for i in columns_index_type:
                # is searchable
                if getattr(self.datatable, f'column_{i}_searchable'):
                    column, data_type = columns_index_type[i]
                    if type(self.datatable.search_value) != data_type:
                        search_parameters.append(cast(column, String).contains(self.datatable.search_value))

                    else:
                        search_parameters.append(column.contains(self.datatable.search_value))

        records = records.filter(or_(*search_parameters))

        # order
        if getattr(self.datatable, f'column_{self.datatable.ordered_column}_orderable'):
            if self.datatable.order_direction == 'desc':
                records = records.order_by(desc(ordered_column))

            else:
                records = records.order_by(ordered_column)

        records_count = records.count()
        if self.datatable.page_length < 0:  # user wants to see all records
            self.datatable.page_length = records_count

        paginate = records.paginate(self.datatable.pagination_page, per_page=self.datatable.page_length)
        return paginate.items, paginate.total
