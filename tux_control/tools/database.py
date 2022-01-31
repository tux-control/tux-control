import sqlalchemy
from sqlalchemy import or_, cast
from sqlalchemy.types import String


def truncate(session, table_name: str) -> None:
    truncate_query = sqlalchemy.text('TRUNCATE TABLE {}'.format(table_name))
    session.execute(truncate_query)


def get_attribute_by_dot_notation(model, dot_notation: str):
    names = dot_notation.split('.')
    for column_name in names:
        model = getattr(model, column_name)

    return model


def sort_to_sqlalchemy(column_name: str, order: int, allowed_columns: dict, default_column: str):
    column = allowed_columns.get(column_name, default_column)
    sort_function = {
        1: lambda c: c.asc(),
        -1: lambda c: c.desc()
    }.get(int(order), lambda c: c.asc())

    return sort_function(column)


def filter_to_sqlalchemy(filter_data: dict, allowed_columns: dict, global_columns: dict = None) -> list:
    default_match_mode = 'contains'
    if not global_columns:
        global_columns = allowed_columns

    filter_modes = {
        'startsWith': lambda column, value: column.ilike("{}%".format(value)),
        'contains': lambda column, value: column.ilike("%{}%".format(value)),
        'endsWith': lambda column, value: column.ilike("%{}".format(value)),
        'equals': lambda column, value: column == value,
        'notEquals': lambda column, value: column != value,
        'in': lambda column, value: column.in_(value),
        'lt': lambda column, value: column < value,
        'lte': lambda column, value: column <= value,
        'gt': lambda column, value: column > value,
        'gte': lambda column, value: column >= value
    }

    filter_list = []

    def resolve_filter(filter_function, column_name, filter_value):
        return filter_function(column_name, filter_value)

    for filter_name, filter_parameters in filter_data.items():
        match_mode = filter_parameters.get('match_mode', default_match_mode)
        if match_mode not in filter_modes.keys():
            match_mode = default_match_mode
        filter_function = filter_modes.get(match_mode)

        if filter_name == 'global':
            filter_list_or = []
            for column_name in set(global_columns.values()):
                filter_list_or.append(resolve_filter(filter_function, cast(column_name, String), filter_parameters['value']))
            filter_list.append(or_(*filter_list_or))
        else:
            column_info = allowed_columns.get(filter_name)
            if type(column_info) == dict:
                column_name = column_info.get('column')
                value = column_info.get('deserializer', lambda v: v)(filter_parameters['value'])
            else:
                column_name = column_info
                value = filter_parameters['value']
            if column_name:
                cast_to = {
                    'startsWith': String,
                    'contains': String,
                    'endsWith': String,
                }.get(match_mode)

                if cast_to:
                    filter_list.append(resolve_filter(filter_function, cast(column_name, cast_to), value))
                else:
                    filter_list.append(resolve_filter(filter_function, column_name, value))

    return filter_list
