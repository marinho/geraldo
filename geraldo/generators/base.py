class ReportGenerator(object):
    """A report generator is used to generate a report to a specific format."""

    def __init__(self, report):
        """This method should be overrided to receive others arguments"""
        self.report = report

    def execute(self):
        """This method must be overrided to execute the report generation."""
        pass

