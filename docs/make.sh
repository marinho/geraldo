#!/bin/sh

echo "Generating HTML from Sphinx..."
make html

echo "Copying output files to site docs folder..."
cp build/html/*.html ../site/newsite/site-geraldo/docs/
cp build/html/*.js ../site/newsite/site-geraldo/docs/
cp build/html/*.inv ../site/newsite/site-geraldo/docs/
cp build/html/_sources/*.txt ../site/newsite/site-geraldo/docs/_sources/
cp build/html/_sources/examples/*.txt ../site/newsite/site-geraldo/docs/_sources/examples/
cp build/html/_static/*.css ../site/newsite/site-geraldo/docs/_static/
cp build/html/_static/*.js ../site/newsite/site-geraldo/docs/_static/
cp build/html/_static/*.png ../site/newsite/site-geraldo/docs/_static/
cp build/html/examples/*.html ../site/newsite/site-geraldo/docs/examples/

echo "Done!"
