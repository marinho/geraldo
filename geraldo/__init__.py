VERSION = (0, 1, 'yet_a_baby')

def get_version():
    return '%d.%d-%s'%VERSION

__author__ = 'Marinho Brandao'
__license__ = 'GNU Lesser General Public License (LGPL)'
__url__ = 'http://github.com/marinho/django-geraldo/'
__version__ = get_version()

from base import Report, ReportBand, TableBand, ReportGroup
from widgets import Label, ObjectValue, SystemField
from widgets import FIELD_ACTION_VALUE, FIELD_ACTION_COUNT, FIELD_ACTION_AVG,\
        FIELD_ACTION_MIN, FIELD_ACTION_MAX, FIELD_ACTION_SUM,\
        FIELD_ACTION_DISTINCT_COUNT, BAND_WIDTH
from graphics import RoundRect, Rect, Line, Circle, Arc, Ellipse, Image
