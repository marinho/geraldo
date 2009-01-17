# TODO

from base import ReportGenerator

class XMLStructGenerator(ReportGenerator):
    """This is an **exporter** to output a XML format, with the goal to be
    used to import/export report classes. It ignores the queryset and just
    works with save/load the structure into a file.
    
    Would be nice use it also in a friendly JavaScript graphic tool to edit
    reports."""
    filename = None

    def __init__(self, report, filename):
        super(XMLStructGenerator, self).__init__(report, *args, **kwargs)

        self.filename = filename

    def execute(self):
        pass

