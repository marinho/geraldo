# Geraldo setup

import os.path
# Downloads setuptools if not find it before try to import
try:
    from setuptools import setup, find_packages
except:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from setuptools import setup

# Importing geraldo.version.get_version here would cause an attempt to import
# `reportlab` (via, e.g., geraldo.graphics, imported from geraldo.__init__).
# So we execfile the module directly instead, since it has no dependencies.
execfile(os.path.join(os.path.dirname(__file__), "geraldo", "version.py"))

setup(
    name = 'Geraldo',
    version = get_version(),
    description = 'Geraldo is a reports engine for Python and Django applications',
    long_description = 'Geraldo is a Python and Django pluggable application that works with ReportLab to generate complex reports.',
    author = 'Marinho Brandao',
    author_email = 'marinho@gmail.com',
    url = 'http://www.geraldoreports.org/',
    #download_url = 'http://ufpr.dl.sourceforge.net/sourceforge/geraldo/Geraldo-0.2-stable.tar.gz',
    license = 'GNU Lesser General Public License (LGPL)',
    packages = ['geraldo', 'geraldo.tests', 'geraldo.generators',],
    install_requires = ['reportlab',],
)
