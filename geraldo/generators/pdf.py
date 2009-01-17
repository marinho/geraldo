# TODO

from base import ReportGenerator

class PDFGenerator(ReportGenerator):
    """This is a generator to output a PDF using ReportLab library with
    preference by its Platypus API"""
    filename = None

    def __init__(self, report, filename):
        super(PDFGenerator, self).__init__(report, *args, **kwargs)

        self.filename = filename

    def execute(self):
        pass


