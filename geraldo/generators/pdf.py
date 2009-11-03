import datetime, os
from base import ReportGenerator

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.lib.units import cm

try:
    # Try to import pyPdf, a library to combine lots of PDF files
    # at once. It is important to improve Geraldo's performance
    # on memory consumming when generating large files.
    # http://pypi.python.org/pypi/pyPdf/
    import pyPdf
except ImportError:
    pyPdf = None

DEFAULT_TEMP_DIR = '/tmp/'

from geraldo.utils import get_attr_value, calculate_size
from geraldo.widgets import Widget, Label, SystemField
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc,\
        Ellipse, Image

class PDFGenerator(ReportGenerator):
    """This is a generator to output a PDF using ReportLab library with
    preference by its Platypus API"""
    filename = None
    canvas = None
    return_canvas = False

    multiple_canvas = bool(pyPdf)
    temp_files = None
    temp_file_name = None
    temp_files_counter = 0
    temp_files_max_pages = 10
    temp_directory = DEFAULT_TEMP_DIR

    def __init__(self, report, filename=None, canvas=None, return_canvas=False,
            multiple_canvas=None, temp_directory=None):
        super(PDFGenerator, self).__init__(report)

        self.filename = filename
        self.canvas = canvas
        self.return_canvas = return_canvas
        self.temp_directory = temp_directory or self.temp_directory

        # Sets multiple_canvas with default value if None
        if multiple_canvas is not None:
            self.multiple_canvas = multiple_canvas

        # Sets multiple_canvas as False if a canvas has been informed as argument
        # nor if return_canvas attribute is setted as True
        if canvas or self.return_canvas:
            self.multiple_canvas = False
            
        # Initializes multiple canvas controller variables
        elif self.multiple_canvas:
            self.temp_files = []
            
            # Just a unique name (current time + id of this object + formatting string for counter + PDF extension)
            self.temp_file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%s') + str(id(self)) + '_%s.pdf'

    def execute(self):
        """Generates a PDF file using ReportLab pdfgen package."""
        super(PDFGenerator, self).execute()

        # Initializes the temporary PDF canvas (just to be used as reference)
        if not self.canvas:
            self.start_canvas()

        # Render pages
        self.render_bands()

        # Initializes the definitive PDF canvas
        self.start_pdf()

        # Generate the report pages (here it happens)
        self.generate_pages()

        if self.multiple_canvas:
            self.combine_multiple_canvas()

        else:
            # Returns the canvas
            if self.return_canvas:
                return self.canvas

            # Saves the canvas - only if it didn't return it
            self.close_current_canvas()

    def start_canvas(self, filename=None):
        """Sets the PDF canvas"""

        # Canvas for multiple canvas
        if self.multiple_canvas:
            filename = os.path.join(
                    self.temp_directory,
                    filename or self.temp_file_name%(self.temp_files_counter),
                    )

            # Appends this filename to the temp files list
            self.temp_files.append(filename)

            # Increments the counter for the next file
            self.temp_files_counter += 1

            self.canvas = Canvas(filename=filename, pagesize=self.report.page_size)

        # Canvas for single canvas
        else:
            filename = filename or self.filename
            self.canvas = Canvas(filename=filename, pagesize=self.report.page_size)

    def close_current_canvas(self):
        """Saves and close the current canvas instance"""
        self.canvas.save()

    def combine_multiple_canvas(self):
        """Combine multiple PDF files at once when is working with multiple canvas"""
        if not self.multiple_canvas or not pyPdf or not self.temp_files:
            return

        readers = []
        def append_pdf(input, output):
            for page_num in range(input.numPages):
                output.addPage(input.getPage(page_num))

        output = pyPdf.PdfFileWriter()
        for f_name in self.temp_files:
            reader = pyPdf.PdfFileReader(file(f_name, 'rb'))
            readers.append(reader)

            append_pdf(reader, output)

        if isinstance(self.filename, basestring):
            fp = file(self.filename, 'wb')
        else:
            fp = self.filename
        
        output.write(fp)

        # Closes and clear objects
        fp.close()
        for r in readers: del r
        del output

    def start_pdf(self):
        """Initializes the PDF document with some properties and methods"""
        # Set PDF properties
        self.canvas.setTitle(self.report.title)
        self.canvas.setAuthor(self.report.author)
        self.canvas.setSubject(self.report.subject)
        self.canvas.setKeywords(self.report.keywords)

    def render_page_header(self):
        """Generate the report page header band if it exists"""
        if not self.report.band_page_header:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_page_header.visible:
            return

        # Call method that print the band area and its widgets
        self.render_band(
                self.report.band_page_header,
                top_position=self.calculate_size(self.report.page_size[1]) - self.calculate_size(self.report.margin_top),
                update_top=False,
                )

    def render_page_footer(self):
        """Generate the report page footer band if it exists"""
        if not self.report.band_page_footer:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_page_footer.visible:
            return

        # Call method that print the band area and its widgets
        self.render_band(
                self.report.band_page_footer,
                top_position=self.calculate_size(self.report.margin_bottom) +\
                    self.calculate_size(self.report.band_page_footer.height),
                update_top=False,
                )

    def calculate_top(self, *args):
        ret = args[0]

        for i in args[1:]:
            ret -= i

        return ret

    def get_top_pos(self):
        """Since the coordinates are bottom-left on PDF, we have to use this to get
        the current top position, considering also the top margin."""
        ret = self.calculate_size(self.report.page_size[1]) - self.calculate_size(self.report.margin_top) - self._current_top_position

        if self.report.band_page_header:
            ret -= self.calculate_size(self.report.band_page_header.height)

        return ret

    def make_paragraph(self, text, style=None):
        """Uses the Paragraph class to return a new paragraph object"""
        return Paragraph(text, style)

    def wrap_paragraph_on(self, paragraph, width, height):
        """Wraps the paragraph on the height/width informed"""
        paragraph.wrapOn(self.canvas, width, height)

    # Stylizing

    def set_fill_color(self, color):
        """Sets the current fill on canvas. Used for fonts and shape fills"""
        self.canvas.setFillColor(color)
    
    def set_stroke_color(self, color):
        """Sets the current stroke on canvas"""
        self.canvas.setStrokeColor(color)

    def set_stroke_width(self, width):
        """Sets the stroke/line width for shapes"""
        self.canvas.setLineWidth(width)

    def make_paragraph_style(self, band, style=None):
        """Merge report default_style + band default_style + widget style"""
        d_style = self.report.default_style.copy()

        if band.default_style:
            for k,v in band.default_style.items():
                d_style[k] = v

        if style:
            for k,v in style.items():
                d_style[k] = v

        return ParagraphStyle(name=datetime.datetime.now().strftime('%H%M%S'), **d_style)

    def keep_in_frame(self, widget, width, height, paragraphs, mode, persistent=False):
        keep = KeepInFrame(width, height, paragraphs, mode=mode)
        keep.canv = self.canvas
        keep.wrap(self.calculate_size(widget.width), self.calculate_size(widget.height))

        if persistent:
            widget.keep = keep

        return keep

    # METHODS THAT ARE TOTALLY SPECIFIC TO THIS GENERATOR AND MUST
    # OVERRIDE THE SUPERCLASS EQUIVALENT ONES

    def generate_pages(self):
        """Specific method that generates the pages"""
        self._generation_datetime = datetime.datetime.now()

        for num, page in enumerate([page for page in self._rendered_pages if page.elements]):
            self._current_page_number = num + 1

            # Multiple canvas support (closes current and creates a new
            # once if reaches the max pages for temp file)
            if num and self.multiple_canvas and num%self.temp_files_max_pages == 0:
                self.close_current_canvas()
                del self.canvas
                self.start_canvas()

            # Loop at band widgets
            for element in page.elements:
                # Widget element
                if isinstance(element, Widget):
                    widget = element
    
                    # Set element colors
                    self.set_fill_color(widget.font_color)
    
                    self.generate_widget(widget, self.canvas, num)
    
                # Graphic element
                elif isinstance(element, Graphic):
                    graphic = element
    
                    # Set element colors
                    self.set_fill_color(graphic.fill_color)
                    self.set_stroke_color(graphic.stroke_color)
                    self.set_stroke_width(graphic.stroke_width)
    
                    self.generate_graphic(graphic, self.canvas)

            self.canvas.showPage()

        # Multiple canvas support (closes the current one)
        if self.multiple_canvas:
            self.close_current_canvas()
            del self.canvas

    def generate_widget(self, widget, canvas=None, page_number=0):
        """Renders a widget element on canvas"""
        if isinstance(widget, SystemField):
            # Sets system fields
            widget.fields['report_title'] = self.report.title
            widget.fields['page_number'] = page_number + 1
            widget.fields['page_count'] = self.get_page_count()
            widget.fields['current_datetime'] = self._generation_datetime
            widget.fields['report_author'] = self.report.author

        # This includes also the SystemField above
        if isinstance(widget, Label):
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

        #elif isinstance(widget, Label):
        #    if widget.truncate_overflow:
        #        widget.keep.drawOn(canvas, widget.left, widget.top)
        #    else:
        #        widget.para.drawOn(canvas, widget.left, widget.top)

    def generate_graphic(self, graphic, canvas=None):
        """Renders a graphic element"""
        canvas = canvas or self.canvas

        if isinstance(graphic, RoundRect):
            canvas.roundRect(
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    graphic.radius,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Rect):
            canvas.rect(
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Line):
            canvas.line(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    )
        elif isinstance(graphic, Circle):
            canvas.circle(
                    graphic.left_center,
                    graphic.top_center,
                    graphic.radius,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Arc):
            canvas.arc(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    graphic.start_angle,
                    graphic.extent,
                    )
        elif isinstance(graphic, Ellipse):
            canvas.ellipse(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Image) and graphic.image:
            canvas.drawInlineImage(
                    graphic.image,
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    )

