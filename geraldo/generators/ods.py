"""Package with ODS generator. ODS is short name for Open Document Sheet, ISO-standard and
commonly used by OpenOffice, KOffice and others office suites.

ODS files are commonly used in replacement to XLS Excel files and can be converted to be
one of them.

Depends on ODFpy library ( http://odfpy.forge.osor.eu/ )"""

import datetime

from base import ReportGenerator
from geraldo.widgets import Widget, Label, SystemField
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc, Ellipse, Image
from geraldo.barcodes import BarCode

DEFAULT_TEMP_DIR = '/tmp/'

try:
    import odf
    from odf.opendocument import OpenDocumentSpreadsheet
    import odf.style
    import odf.number
    import odf.text
    import odf.table
except ImportError:
    odf = None

class Paragraph(object):
    text = ''
    style = None
    height = None
    width = None

    def __init__(self, text, style=None):
        self.text = text
        self.style = style

    def wrapOn(self, page_size, width, height): # TODO: this should be more eficient with multiple lines
        self.height = height
        self.width = width

class ODSGenerator(ReportGenerator):
    """This is a generator to output a ODS document sheet using ODFpy library"""

    filename = None
    render_page_header_only_first_page = True
    render_page_footer_only_last_page = True

    # Document-specific attributes
    doc = None
    _current_table = None

    def __init__(self, report, filename=None, cache_enabled=None, **kwargs):
        # Exception if doesn't find ODFpy
        if not odf:
            raise Exception('ODFpy has been not found. Please download it from http://odfpy.forge.osor.eu/ and install.')

        super(ODSGenerator, self).__init__(report)

        self.filename = filename

        # Cache enabled
        if cache_enabled is not None:
            self.cache_enabled = cache_enabled
        elif self.cache_enabled is None:
            self.cache_enabled = bool(self.report.cache_status)

    def execute(self):
        """Generates a ODS file using ODFpy library."""
        super(ODSGenerator, self).execute()

        # Check the cache
        if self.cached_before_render():
            return

        # Prepare additional fonts
        self.prepare_additional_fonts()

        # Calls the before_print event
        self.report.do_before_print(generator=self)

        # Render pages
        self.render_bands()

        # Check the cache
        if self.cached_before_generate():
            return
 
        # Calls the after_render event
        self.report.do_before_generate(generator=self)

        # Initializes the definitive ODS document
        self.start_doc()

        # Generate the report pages (here it happens)
        self.generate_pages()

        # Calls the after_print event
        self.report.do_after_print(generator=self)

        # Saves the document
        self.close_doc()

        # Store in the cache
        self.store_in_cache()

    def get_hash_key(self, objects):
        """Appends pdf extension to the hash_key"""
        return super(ODSGenerator, self).get_hash_key(objects) + '.ods'

    def start_doc(self):
        """Initializes spreadsheet document in attribute self.doc"""
        self.doc = OpenDocumentSpreadsheet()
        self._current_table = odf.table.Table(name=self.report.title)

    def close_doc(self):
        """Closes document instance and saves it in the file"""
        self.doc.spreadsheet.addElement(self._current_table)
        self.doc.save(self.filename)

    def prepare_additional_fonts(self): # TODO
        """This method will prepare fonts before use them in the spreadsheet"""
        pass

    def make_paragraph_style(self, band, style=None):
        d_style = self.report.default_style.copy()

        if band.default_style:
            for k,v in band.default_style.items():
                d_style[k] = v

        if style:
            for k,v in style.items():
                d_style[k] = v

        import datetime

        return dict(name=datetime.datetime.now().strftime('%H%m%s'), **d_style)

    def make_paragraph(self, text, style=None):
        """Uses the class P to return a new paragraph object"""
        return Paragraph(text, style)

    def wrap_paragraph_on(self, paragraph, width, height):
        """Wraps the paragraph on the height/width informed"""
        paragraph.wrapOn(self.report.page_size, width, height)

    def store_in_cache(self):
        if not self.cache_enabled or self.report.cache_status == CACHE_DISABLED:
            return

        # TODO

    # METHODS THAT ARE TOTALLY SPECIFIC TO THIS GENERATOR AND MUST
    # OVERRIDE THE SUPERCLASS EQUIVALENT ONES

    def generate_pages(self):
        """Specific method that generates the pages"""
        self._generation_datetime = datetime.datetime.now()

        for num, page in enumerate([page for page in self._rendered_pages if page.elements]):
            self._current_page_number = num + 1

            # Loop at band widgets
            for element in page.elements:
                # Widget element
                if isinstance(element, Widget):
                    widget = element
    
                    # Set element colors
                    self.set_fill_color(widget.font_color)
    
                    self.generate_widget(widget, self.doc, num)
    
                # Graphic element
                elif isinstance(element, Graphic):
                    graphic = element
    
                    # Set element colors
                    self.set_fill_color(graphic.fill_color)
                    self.set_stroke_color(graphic.stroke_color)
                    self.set_stroke_width(graphic.stroke_width)
    
                    self.generate_graphic(graphic, self.doc)

    def generate_widget(self, widget, canvas=None, page_number=0): # TODO
        """Renders a widget element on canvas"""
        if isinstance(widget, SystemField):
            # Sets system fields
            widget.fields['report_title'] = self.report.title
            widget.fields['page_number'] = page_number + 1
            widget.fields['page_count'] = self.get_page_count()
            widget.fields['current_datetime'] = self._generation_datetime
            widget.fields['report_author'] = self.report.author

        # Calls the before_print event
        widget.do_before_print(generator=self)

        # Exits if is not visible
        if not widget.visible:
            return

        # This includes also the SystemField above
        if isinstance(widget, Label):
            # TODO
            pass
            """
            para = Paragraph(widget.text, self.make_paragraph_style(widget.band, widget.style))
            para.wrapOn(canvas, widget.width, widget.height)

            if widget.truncate_overflow:
                keep = self.keep_in_frame(
                        widget,
                        self.calculate_size(widget.width),
                        self.calculate_size(widget.height),
                        [para],
                        mode='truncate',
                        )
                keep.drawOn(canvas, widget.left, widget.top)
            elif isinstance(widget, SystemField):
                para.drawOn(canvas, widget.left, widget.top - para.height)
            else:
                para.drawOn(canvas, widget.left, widget.top)
            """

            # Calls the after_print event
            widget.do_after_print(generator=self)

    def generate_graphic(self, graphic, canvas=None): # TODO
        pass

