"""Package with ODS generator. ODS is short name for Open Document Sheet, ISO-standard and
commonly used by OpenOffice, KOffice and others office suites.

ODS files are commonly used in replacement to XLS Excel files and can be converted to be
one of them.

Depends on ODFpy library ( http://odfpy.forge.osor.eu/ )"""

from base import ReportGenerator

DEFAULT_TEMP_DIR = '/tmp/'

try:
    import odf
    from odf.opendocument import OpenDocumentSpreadsheet
    #from odf.style import Style, TextProperties, TableColumnProperties, Map
    #from odf.number import NumberStyle, CurrencyStyle, CurrencySymbol,  Number,  Text
    #from odf.text import P
    #from odf.table import Table, TableColumn, TableRow, TableCell
except ImportError:
    odf = None

class ODSGenerator(ReportGenerator):
    """This is a generator to output a ODS document sheet using ODFpy library"""

    filename = None

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

    def close_doc(self):
        """Closes document instance and saves it in the file"""
        pass

