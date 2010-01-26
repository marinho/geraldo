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
    count = None
    start_left = None
    start_top = None
    visible = True
    element_kwargs = None

    _elements = None

    def __init__(self, element_class, count, start_left=None, start_top=None,
            visible=None, **kwargs):
        self.element_class = element_class
        self.count = count
        self.start_left = start_left is not None and start_left or self.start_left
        self.start_top = start_top is not None and start_top or self.start_top
        self.visible = visible is not None and visible or self.visible

        # Stores the additinal arguments to use when creating the elements
        self.element_kwargs = kwargs.copy()

    def get_elements(self, cross_cols=None):
        if self._elements is None:
            count = self.count

            # Get cross cols
            if not cross_cols and isinstance(self.report.queryset, CrossReferenceMatrix):
                cross_cols = self.report.queryset.cols()

                if count == CROSS_COLS:
                    count = len(cross_cols)

            self._elements = []

            # Loop for count of elements to be created
            for num in range(count):
                kwargs = self.element_kwargs.copy()

                # Set attributes before creation
                for k,v in kwargs.items():
                    if v == CROSS_COLS:
                        try:
                            kwargs[k] = cross_cols[num]
                        except IndexError:
                            kwargs[k] = cross_cols[-1]

                # Create the element
                el = self.element_class(**kwargs)

                # Set attributes after creation
                if self.start_left is not None: # Maybe we should support distance here
                    el.left = self.start_left + el.width * num

                if self.start_top is not None: # Maybe we should support distance here
                    el.top = self.start_top + el.height * num

                self._elements.append(el)

        return self._elements

