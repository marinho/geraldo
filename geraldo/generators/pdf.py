# TODO

from base import ReportGenerator

from reportlab.pdfgen.canvas import Canvas

class PDFGenerator(ReportGenerator):
    """This is a generator to output a PDF using ReportLab library with
    preference by its Platypus API"""
    filename = None

    _is_first_page = True
    _is_latest_page = True
    _current_top_position = 0

    def __init__(self, report, filename):
        super(PDFGenerator, self).__init__(report)

        self.filename = filename

    def execute(self):
        """Generate a PDF file using ReportLab pdfgen package."""

        # Initializes the PDF canvas
        self.start_pdf(self.filename)

        pass

    def start_pdf(self, filename):
        """Initializes the PDF document with some properties and methods"""
        # Sets the PDF canvas
        self.canvas = Canvas(filename=filename)

        # Set PDF properties
        self.canvas.setTitle(self.report.title)
        self.canvas.setAuthor(self.report.author)

        self._is_first_page = True
        self.generate_top()

    def generate_top(self):
        """Generate the report begin band if it exists"""
        if not self.report.band_begin:
            return

    def generate_page_header(self):
        """Generate the report page header band if it exists"""
        pass

    def generate_page_footer(self):
        """Generate the report page footer band if it exists"""
        pass

    def generate_summary(self):
        """Generate the report summary band if it exists"""
        pass

    def start_new_page(self, with_header=True):
        """Do everything necessary to be done to start a new page"""
        if with_header:
            self.generate_page_header()

    def end_current_page(self):
        """Closes the current page, using showPage method. Everything done after
        this will draw into a new page. Before this, using the generate_page_footer
        method to draw the footer"""
        self.generate_page_footer()

        if self._is_latest_page:
            self.generate_summary()

        self.canvas.showPage()

        self._current_page += 1
        self._is_first_page = False
        self.update_top_pos(set=0) # <---- update top position

    def get_top_pos(self):
        """Since the coordinates are bottom-left on PDF, we have to use this to get
        the current top position, considering also the top margin."""
        return self.report.page_size[1] - self.report.margin_top - self._current_top_position

    def get_available_height(self):
        """Returns the available client height area from the current top position
        until the end of page, considering the bottom margin."""
        return self.report.page_size[1] - self.report.margin_bottom - self._current_top_position

    def update_top_pos(self, increase=0, decrease=0, set=None):
        """Updates the current top position controller, increasing (by default),
        decreasing or setting it with a new value."""
        if set is not None:
            self._current_top_position = set
        else:        
            self._current_top_position += increase
            self._current_top_position -= decrease

        return self._current_top_position


