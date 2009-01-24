# Geraldo setup

from distutils.core import setup
from geraldo import get_version

setup(
    name = 'Geraldo',
    version = get_version(),
    description = 'Geraldo is a reports engine for Python and Django applications',
    long_description = 'Geraldo is a Python and Django pluggable application for that works with ReportLab to generate complex reports.',
    author = 'Marinho Brandao',
    author_email = 'marinho@gmail.com',
    url = 'http://github.com/marinho/django-geraldo/',
    download_url = 'http://github.com/marinho/django-geraldo/',
    license = 'GNU Lesser General Public License (LGPL)',
    packages = ['geraldo', 'geraldo.tests', 'geraldo.generators',],
)
