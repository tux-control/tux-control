from typing import Optional
from tux_control.tools.IDictify import IDictify


class GridColumn(IDictify):
    def __init__(self, field: str, header: str, filter_match_mode: Optional[str] = None, is_sortable: bool = False, column_format: str = None):
        self.field = field
        self.header = header
        self.filter_match_mode = filter_match_mode
        self.is_sortable = is_sortable
        self.column_format = column_format

    def to_dict(self) -> dict:
        return {
            'field': self.field,
            'header': self.header,
            'filter_match_mode': self.filter_match_mode,
            'is_sortable': self.is_sortable,
            'column_format': self.column_format
        }
