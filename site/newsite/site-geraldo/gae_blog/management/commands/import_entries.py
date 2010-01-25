from optparse import make_option

from django.core.management import BaseCommand

from gae_blog.migration import import_from_json

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--file',
                default=None,
                dest='filename',
                ),
            )

    def handle(self, filename=None, **kwargs):
        # Get file content
        fp = file(filename)
        data = fp.read()
        fp.close()

        import_from_json(data, show=True)


