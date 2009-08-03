import datetime
from base import ReportGenerator

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.lib.units import cm

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

    def __init__(self, report, filename=None, canvas=None, return_canvas=False):
        super(PDFGenerator, self).__init__(report)

        self.filename = filename
        self.canvas = canvas
        self.return_canvas = return_canvas

    def execute(self):
        """Generates a PDF file using ReportLab pdfgen package."""
        super(PDFGenerator, self).execute()

        # Initializes the temporary PDF canvas (just to be used as reference)
        if not self.canvas:
            self.canvas = Canvas(self.filename, pagesize=self.report.page_size)

        # Render pages
        self.render_bands()

        # Initializes the definitive PDF canvas
        self.start_pdf()

        self.generate_pages()

        # Returns the canvas
        if self.return_canvas:
            return self.canvas

        # Saves the canvas - only if it didn't return it
        self.canvas.save()

    def start_pdf(self, filename=None): # XXX
        """Initializes the PDF document with some properties and methods"""
        # Sets the PDF canvas
        #self.canvas = Canvas(filename=filename, pagesize=self.report.page_size) # XXX

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

    def make_paragraph(self, text, style=None): # XXX
        """Uses the Paragraph class to return a new paragraph object"""
        return Paragraph(text, style)

    def wrap_paragraph_on(self, paragraph, width, height): # XXX
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

        import datetime

        return ParagraphStyle(name=datetime.datetime.now().strftime('%H%M%S'), **d_style)

    def keep_in_frame(self, widget, width, height, paragraphs, mode):
        widget.keep = KeepInFrame(width, height, paragraphs, mode=mode)
        
        widget.keep.canv = self.canvas
        widget.keep.wrap(self.calculate_size(widget.width), self.calculate_size(widget.height))

    # METHODS THAT ARE TOTALLY SPECIFIC TO THIS GENERATOR AND MUST
    # OVERRIDE THE SUPERCLASS EQUIVALENT ONES

    def generate_pages(self):
        """Specific method that generates the pages"""
        self._generation_datetime = datetime.datetime.now()

        for num, page in enumerate([page for page in self._rendered_pages if page.elements]):
            self._current_page_number = num

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

    def generate_widget(self, widget, canvas=None, page_number=0):
        """Renders a widget element on canvas"""
        if isinstance(widget, SystemField):
            # Sets system fields
            widget.fields['report_title'] = self.report.title
            widget.fields['page_number'] = page_number + 1
            widget.fields['page_count'] = self.get_page_count()
            widget.fields['current_datetime'] = self._generation_datetime
            widget.fields['report_author'] = self.report.author

            para = Paragraph(widget.text, self.make_paragraph_style(widget.band, widget.style))
            para.wrapOn(canvas, widget.width, widget.height)
            para.drawOn(canvas, widget.left, widget.top - para.height)
        elif isinstance(widget, Label):
            if widget.truncate_overflow:
                widget.keep.drawOn(canvas, widget.left, widget.top)
            else:
                widget.para.drawOn(canvas, widget.left, widget.top)

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

