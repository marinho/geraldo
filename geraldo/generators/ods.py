"""Package with ODS generator. ODS is short name for Open Document Sheet, ISO-standard and
commonly used by OpenOffice, KOffice and others office suites.

ODS files are commonly used in replacement to XLS Excel files and can be converted to be
one of them."""

from base import ReportGenerator

DEFAULT_TEMP_DIR = '/tmp/'

class ODSGenerator(ReportGenerator):
    """This is a generator to output a ODS document sheet using pyODF library"""

    filename = None

    def __init__(self, report, filename=None, cache_enabled=None, **kwargs):
        super(ODSGenerator, self).__init__(report)

        self.filename = filename

        # Cache enabled
        if cache_enabled is not None:
            self.cache_enabled = cache_enabled
        elif self.cache_enabled is None:
            self.cache_enabled = bool(self.report.cache_status)

    def execute(self):
        """Generates a ODS file using pyODF library."""
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

        # Initializes the definitive PDF canvas
        self.start_output() # XXX

        # Generate the report pages (here it happens)
        self.generate_pages()

        # Calls the after_print event
        self.report.do_after_print(generator=self)

        # Saves the canvas - only if it didn't return it
        self.close_output() # XXX

        # Store in the cache
        self.store_in_cache()

    def get_hash_key(self, objects):
        """Appends pdf extension to the hash_key"""
        return super(ODSGenerator, self).get_hash_key(objects) + '.ods'

