from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

class Report(object):
    """This class must be inherited to be used as a new report.
    
    A report have bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to works properly"""

    # Report properties
    title = ''
    author = ''
    
    # Page dimensions
    page_size = A4
    margin_top = 1*cm
    margin_bottom = 1*cm
    margin_left = 1*cm
    margin_right = 1*cm

    # Bands - is not possible to have more than one band from the same kind
    band_begin = None
    band_summary = None
    band_page_header = None
    band_page_footer = None
    band_detail = None

    # Data source driver
    queryset = None
    print_if_empty = False # This means if a queryset is empty, the report will
                           # be generated or not

    # Colors
    default_font_color = black
    default_stroke_color = black
    default_fill_color = black

    def __init__(self, queryset=None):
        self.queryset = queryset or self.queryset

    def generate_by(self, generator_class, *args, **kwargs):
        """This method uses a generator inherited class to generate a report
        to a wanted format, like XML, HTML or PDF, for example.
        
        The arguments *args and **kwargs are passed to class initializer."""
        generator = generator_class(self, *args, **kwargs)

        return generator.execute()

class ReportBand(object):
    """A band is a horizontal area in the report. It can be used to print
    things on the top, on summary, on page header, on page footer or one time
    per object from queryset."""
    height = 1*cm
    visible = True
    borders = {'top': None, 'right': None, 'bottom': None, 'left': None,
            'all': None}

class TableBand(ReportBand):
    """This band must be used only as a detail band. It doesn't is repeated per
    object, but instead of it is streched and have its rows increased."""
    pass

