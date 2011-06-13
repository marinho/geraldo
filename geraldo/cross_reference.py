"""Functions to make cross reference tables and charts on Geraldo."""

try:
    set
except:
    from sets import Set as set

import random, decimal
from utils import get_attr_value, memoize
from base import ReportBand, GeraldoObject, CROSS_COLS, CROSS_ROWS

RANDOM_ROW_DEFAULT = RANDOM_COL_DEFAULT = ''.join([random.choice([chr(c) for c in range(48, 120)]) for i in range(100)])

class CrossReferenceProxy(object):
    matrix = None
    row = None

    def __init__(self, matrix, row):
        self.matrix = matrix
        self.row = row

    def __getattr__(self, name):
        if name in ('values','max','min','sum','avg','count','distinct_count',
                'first','last','percent',):
            func = getattr(self.matrix, name)
            def _inner(cell, col=RANDOM_COL_DEFAULT):
                return func(cell, self.row, col)
            return _inner

        raise AttributeError()


class CrossReferenceMatrix(object):
    """Encapsulates an objects list and stores the X (rows) and Y (cols) attributes to make
    cross reference matrix, or just to make the calculations required.
    
    Used by detail bands, subreports and charts, and not at all coupled to Geraldo's API.
    
    The objects from this class are iterable."""

    objects_list = None
    rows_attr = None
    rows_values = None
    cols_attr = None
    cols_values = None
    decimal_as_float = False

    def __init__(self, objects_list, rows_attribute, cols_attribute, decimal_as_float=None,
            rows_values=None, cols_values=None):
        self.objects_list = list(objects_list) or []
        self.rows_attr = rows_attribute
        self.cols_attr = cols_attribute
        self.rows_values = rows_values
        self.cols_values = cols_values

        if decimal_as_float is not None:
            self.decimal_as_float = decimal_as_float

    def __iter__(self):
        for row in self.rows():
            yield CrossReferenceProxy(self, row)

    def get_attr_value(self, obj, attr):
        """Returns the attribute value on an object, and converts decimal to float if necessary."""

        value = get_attr_value(obj, attr)
        
        if isinstance(value, decimal.Decimal) and self.decimal_as_float:
            value = float(value)

        return value

    def sort_rows(self, a, b):
        return cmp(a, b)

    def sort_cols(self, a, b):
        return cmp(a, b)

    @memoize
    def rows(self):
        if self.rows_values is None:
            self.rows_values = list(set([self.get_attr_value(obj, self.rows_attr) for obj in self.objects_list]))

            # Sort list by method
            self.rows_values.sort(self.sort_rows)

        return self.rows_values

    @memoize
    def cols(self):
        if self.cols_values is None:
            self.cols_values = list(set([self.get_attr_value(obj, self.cols_attr) for obj in self.objects_list]))

            # Sort list by method
            self.cols_values.sort(self.sort_cols)

        return self.cols_values

    @memoize
    def values(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        """Receives the cell, row and col values and make the cross reference among them."""

        return [self.get_attr_value(obj, cell) for obj in self.objects_list
            if (row == RANDOM_ROW_DEFAULT or self.get_attr_value(obj, self.rows_attr) == row) and
               (col == RANDOM_COL_DEFAULT or self.get_attr_value(obj, self.cols_attr) == col)]

    @memoize
    def max(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        values = self.values(cell, row, col)
        return values and max(values) or None

    @memoize
    def min(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        values = self.values(cell, row, col)
        return values and min(values) or None

    @memoize
    def sum(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        return sum(self.values(cell, row, col))

    @memoize
    def avg(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        values = map(float, self.values(cell, row, col))

        if row == RANDOM_ROW_DEFAULT and col == RANDOM_COL_DEFAULT:
            count = len(values)
        elif row == RANDOM_ROW_DEFAULT:
            count = len(self.rows())
        elif col == RANDOM_COL_DEFAULT:
            count = len(self.cols())
        else:
            count = len(self.rows()) * len(self.cols())

        return values and sum(values) / count or None

    @memoize
    def count(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        return len(self.values(cell, row, col))

    @memoize
    def distinct_count(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        return len(set(self.values(cell, row, col)))

    @memoize
    def percent(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        total = self.sum(cell)
        values = self.values(cell, row, col)
        return total and (sum(values) / total * 100) or None

    @memoize
    def first(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        try:
            return self.values(cell, row, col)[0]
        except IndexError:
            return None

    @memoize
    def last(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        try:
            return self.values(cell, row, col)[-1]
        except IndexError:
            return None

    @memoize
    def matrix(self, cell, func='values', show_rows=False, show_cols=False):
        ret = []

        # Show column names if argument requires
        if show_cols:
            # Show the 0,0 cell (row/column relation)
            prep = show_rows and [''] or []

            ret.append(prep + self.cols())

        func = getattr(self, func)

        for row in self.rows():
            # Show rows values if argument requires
            prep = show_rows and [row] or []
            ret.append(prep + [func(cell, row, col) for col in self.cols()])

        return ret

    @memoize
    def summarize_rows(self, cell, func='values', show_rows=False):
        ret = []

        func = getattr(self, func)

        for row in self.rows():
            val = func(cell, row)

            # Show rows values if argument requires
            if show_rows:
                ret.append([row, val])
            else:
                ret.append(val)

        return ret

    @memoize
    def summarize_cols(self, cell, func='values', show_cols=False):
        ret = []

        func = getattr(self, func)

        for col in self.cols():
            val = func(cell, col=col)

            # Show cols values if argument requires
            if show_cols:
                ret.append([col, val])
            else:
                ret.append(val)

        return ret

