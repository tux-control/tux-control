from math import ceil
from tux_control.tools.IDictify import IDictify


class PaginationList(IDictify):
    def __init__(self, items_all: list, page, per_page, total, items):
        self.items_all = items_all
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0 or self.total is None:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        return PaginationList.paginate(self.items_all, self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""

        return PaginationList.paginate(self.items_all, self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def to_dict(self):
        return {
            'has_next': self.has_next,
            'has_prev': self.has_prev,
            'next_num': self.next_num,
            'prev_num': self.prev_num,
            'page': self.page,
            'pages': self.pages,
            'per_page': self.per_page,
            'total': self.total,
            'data': self.items,
        }

    @staticmethod
    def paginate(items: list, page=None, per_page=None, error_out=True, max_per_page=None, count=True):

        if page is None:
            page = 1

        if per_page is None:
            per_page = 20

        if max_per_page is not None:
            per_page = min(per_page, max_per_page)

        if page < 1:
            if error_out:
                raise ValueError
            else:
                page = 1

        if per_page < 0:
            if error_out:
                raise ValueError
            else:
                per_page = 20

        offset = (page - 1) * per_page
        items_paged = items[offset * -1:][:per_page]

        if not items_paged and page != 1 and error_out:
            raise ValueError

        if not count:
            total = None
        else:
            total = len(items)

        return PaginationList(items, page, per_page, total, items_paged)