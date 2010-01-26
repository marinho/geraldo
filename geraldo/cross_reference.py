"""Functions to make cross reference tables and charts on Geraldo."""

try:
    set
except:
    from sets import Set as set

import random
from utils import get_attr_value, memoize
from base import ReportBand, GeraldoObject

RANDOM_ROW_DEFAULT = RANDOM_COL_DEFAULT = ''.join([random.choice([chr(c) for c in range(48, 120)]) for i in range(100)])
CROSS_COLS = 'cross-cols'

class CrossReferenceProxy(object):
    matrix = None
    row = None

    def __init__(self, matrix, row):
        self.matrix = matrix
        self.row = row

    def values(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.values(cell, self.row, col)

    @memoize
    def max(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.max(cell, self.row, col)

    @memoize
    def min(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.min(cell, self.row, col)

    @memoize
    def sum(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.sum(cell, self.row, col)

    @memoize
    def avg(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.avg(cell, self.row, col)

    @memoize
    def count(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.count(cell, self.row, col)

    @memoize
    def distinct_count(self, cell, col=RANDOM_COL_DEFAULT):
        return self.matrix.distinct_count(cell, self.row, col)


class CrossReferenceMatrix(object):
    """Encapsulates an objects list and stores the X (rows) and Y (cols) attributes to make
    cross reference matrix, or just to make the calculations required.
    
    Used by detail bands, subreports and charts, and not at all coupled to Geraldo's API.
    
    The objects from this class are iterable."""

    objects_list = None
    rows_attr = None
    cols_attr = None

    def __init__(self, objects_list, rows_attribute, cols_attribute):
        self.objects_list = objects_list
        self.rows_attr = rows_attribute
        self.cols_attr = cols_attribute

    def __iter__(self):
        for row in self.rows():
            yield CrossReferenceProxy(self, row)

    @memoize
    def rows(self):
        return list(set([get_attr_value(obj, self.rows_attr) for obj in self.objects_list]))

    @memoize
    def cols(self):
        return list(set([get_attr_value(obj, self.cols_attr) for obj in self.objects_list]))

    @memoize
    def values(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        """Receives the cell, row and col values and make the cross reference among them."""

        return [get_attr_value(obj, cell) for obj in self.objects_list
            if (row == RANDOM_ROW_DEFAULT or get_attr_value(obj, self.rows_attr) == row) and
               (col == RANDOM_COL_DEFAULT or get_attr_value(obj, self.cols_attr) == col)]

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
        values = self.values(cell, row, col)
        return values and sum(values) / len(values) or None

    @memoize
    def count(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        return len(self.values(cell, row, col))

    @memoize
    def distinct_count(self, cell, row=RANDOM_ROW_DEFAULT, col=RANDOM_COL_DEFAULT):
        return len(set(self.values(cell, row, col)))

    @memoize
    def matrix(self, cell, func='values'):
        ret = []

        ret.append([''] + self.cols())

        func = getattr(self, func)

        for row in self.rows():
            ret.append([row] + [func(cell, row, col) for col in self.cols()])

        return ret

class CrossReferenceBand(ReportBand):
    pass

class ManyElements(GeraldoObject):
    """Class that makes the objects creation more dynamic.
    
    This will be moved to other file in the future, since it is not coupled to
    cross reference functions."""

    element_class = None
    start_left = 0
    start_top = 0

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Stores the additinal arguments to use when creating the elements
        self.element_kwargs = kwargs.copy()
        self.element_kwargs.pop('element_class', None)
        self.element_kwargs.pop('start_left', None)
        self.element_kwargs.pop('start_top', None)

