import sys

try:
    import reportlab
except ImportError:
    cm = 28.346456692913385
    A4 = (595.275590551181, 841.8897637795275)
    black = None
    TA_LEFT, TA_CENTER, TA_RIGHT = 0, 1, 2
    landscape = lambda t:(t[1],t[0])
else:
    from reportlab.lib.units import * # Check this - is the source of units
    from reportlab.lib.pagesizes import * # Check this - is the source of page sizes
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT # Check this also
    from reportlab.lib.colors import black

from exceptions import AttributeNotFound

try:
    from functools import wraps
except ImportError:
    wraps = lambda func: func

# FLAGS

BAND_WIDTH = 'band-width'
BAND_HEIGHT = 'band-height'
CROSS_COLS = 'cross-cols'
CROSS_ROWS = 'cross-rows'

FIELD_ACTION_VALUES = 'values'  # \
FIELD_ACTION_FIRST = 'first'    #  > Used only by cross reference functions
FIELD_ACTION_LAST = 'last'      # /
FIELD_ACTION_VALUE = 'value'
FIELD_ACTION_COUNT = 'count'
FIELD_ACTION_AVG = 'avg'
FIELD_ACTION_MIN = 'min'
FIELD_ACTION_MAX = 'max'
FIELD_ACTION_SUM = 'sum'
FIELD_ACTION_DISTINCT_COUNT = 'distinct_count'
FIELD_ACTION_PERCENT = 'percent'

SYSTEM_FIELD_CHOICES = {
    'report_title': 'ReportTitle',
    'page_number': 'PageNumber',
    'page_count': 'PageCount',
    'current_datetime': 'CurrentDateTime',
    'report_author': 'Author',
}

def _get_memoized_value(func, args, kwargs):
    """Used internally by memoize decorator to get/store function results"""
    key = (repr(args), repr(kwargs))
    
    if not key in func._cache_dict:
        ret = func(*args, **kwargs)
        func._cache_dict[key] = ret

    return func._cache_dict[key]

def memoize(func):
    """Decorator that stores function results in a dictionary to be used on the
    next time that the same arguments were informed."""

    func._cache_dict = {}

    def _inner(*args, **kwargs):
        return _get_memoized_value(func, args, kwargs)

    if sys.version.startswith('2.4'):
        return _inner
    else:
        return wraps(func)(_inner)

def get_attr_value(obj, attr_path):
    """This function gets an attribute value from an object. If the attribute
    is a method with no arguments (or arguments with default values) it calls
    the method. If the expression string has a path to a child attribute, it
    supports.
    
    Examples:
        
        attribute_name = 'name'
        attribute_name = 'name.upper'
        attribute_name = 'customer.name.lower'
    """
    if not attr_path:
        raise Exception('Invalid attribute path \'%s\''%attr_path)

    parts = attr_path.split('.')

    try:
        val = getattr(obj, parts[0])
    except AttributeError:
        try:
            val = obj[parts[0]]
        except (KeyError, TypeError):
            raise AttributeNotFound('There is no attribute nor key "%s" in the object "%s"'%(parts[0], repr(obj)))

    if len(parts) > 1:
        val = get_attr_value(val, '.'.join(parts[1:]))

    if callable(val):
        val = val()
        
    return val

@memoize
def calculate_size(size):
    """Calculates the informed size. If this is a string or unicode, it is
    converted to float using evaluation function"""
    if isinstance(size, basestring):
        return eval(size) # If you are thinking this is a semanthic bug, you must
                          # be aware this 'eval' is necessary to calculate sizes
                          # like '10*cm' or '15.8*rows'
                          # I want to check if eval is better way to do it than
                          # do a regex matching and calculate. TODO
    
    return size

# Replaced by ReportLab landscape and portrait functions
#@memoize
#def landscape(page_size):
#    return page_size[1], page_size[0]

@memoize
def format_date(date, expression):
    return date.strftime(expression)

# Tries to import class Process from multiprocessing library and sets
# it as None if import fails
try:
    from multiprocessing import Process
except ImportError:
    Process = None

# Sets this to True if you don't want to use multiprocessing on
# functions with 'run_under_process' decorator
DISABLE_MULTIPROCESSING = False

def run_under_process(func):
    """This is a decorator that uses multiprocessing library to run a
    function under a new process. To use it on Python 2.4 you need to
    install python-multiprocessing package.
    
    Just remember that Process doesn't support returning value"""

    def _inner(*args, **kwargs):
        # If multiprocessing is disabled, just runs function with
        # its arguments
        if not Process or DISABLE_MULTIPROCESSING:
            func(*args, **kwargs)

        prc = Process(target=func, args=args, kwargs=kwargs)
        prc.start()
        prc.join()

    return _inner

