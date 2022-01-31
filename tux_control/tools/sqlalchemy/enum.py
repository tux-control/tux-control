
import enum
import typing
from sqlalchemy.types import TypeDecorator, INTEGER, VARCHAR


class StringEnum(TypeDecorator):
    """

  """
    impl = VARCHAR

    def __init__(self, enum_class: typing.Type[enum.Enum], **kwargs):
        super(StringEnum, self).__init__(**kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            if value not in self.enum_class:
                raise ValueError('Value {} is not member of {}'.format(value, type(self.enum_class)))

            try:
                if isinstance(value, enum.Enum):
                    return value.value
                else:
                    return str(value)
            except ValueError:
                raise ValueError('Only string enums are supported!')

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            # Convert to enum
            return self.enum_class(value)


class IntegerEnum(TypeDecorator):
    """

  """
    impl = INTEGER

    """
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))
    """

    def __init__(self, enum_class: typing.Type[enum.Enum], **kwargs):
        super(IntegerEnum, self).__init__(**kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, enum.Enum) and value not in self.enum_class:
                raise ValueError('Value {} is not member of {}'.format(value, type(self.enum_class)))

            if isinstance(value, int) and value not in list(self.enum_class):
                raise ValueError('Value {} is not member of {}'.format(value, type(self.enum_class)))

            try:
                if isinstance(value, enum.Enum):
                    return value.value
                else:
                    return int(value)
            except ValueError:
                raise ValueError('Only integer enums are supported!')

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            # Convert to enum
            return self.enum_class(value)
