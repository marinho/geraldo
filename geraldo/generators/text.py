from base import ReportGenerator

# In development

class TextGenerator(ReportGenerator):
    """This is a generator to output data in text/plain format."""

    def __init__(self, report):
        super(TextGenerator, self).__init__(report)

    def execute(self):
        rows = []

        # Page header
        # Report top
        # Details
        # Report summary
        # Page footer

        return u'\r'.join(rows)

