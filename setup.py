# Geraldo setup

# Downloads setuptools if not find it before try to import
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from geraldo import get_version

setup(
    name = 'Geraldo',
    version = get_version(),
    description = 'Geraldo is a reports engine for Python and Django applications',
    long_description = 'Geraldo is a Python and Django pluggable application that works with ReportLab to generate complex reports.',
    author = 'Marinho Brandao',
    author_email = 'marinho@gmail.com',
    url = 'http://geraldo.sourceforge.net/',
    #download_url = 'http://ufpr.dl.sourceforge.net/sourceforge/geraldo/Geraldo-0.2-stable.tar.gz',
    license = 'GNU Lesser General Public License (LGPL)',
    packages = ['geraldo', 'geraldo.tests', 'geraldo.generators',],
    #install_requires = ['reportlab','pil'],
)
