#!/usr/bin/env python
"""This tool just converts reStructureText documentation to HTML files"""

import glob
from docutils.core import publish_parts

files = glob.glob('*.txt')

for filename in files:
    # Loads text file
    fp_text = file(filename)
    text = fp_text.read()
    fp_text.close()

    # Converts to HTML
    parts = publish_parts(text, writer_name='html')
    html = parts['whole']

    # Outputs the HTML file
    fp_html = file(filename.replace('.txt', '.html'), 'w')
    fp_html.write(html)
    fp_html.close()

