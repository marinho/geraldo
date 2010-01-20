#!/bin/sh

echo "Generating HTML from Sphinx..."
make html

echo "Copying output files to site docs folder..."
cp build/html/*.html ../site/online/docs/
cp build/html/*.js ../site/online/docs/
cp build/html/*.inv ../site/online/docs/
cp build/html/_sources/*.txt ../site/online/docs/_sources/
cp build/html/_sources/examples/*.txt ../site/online/docs/_sources/examples/
cp build/html/_static/*.css ../site/online/docs/_static/
cp build/html/_static/*.js ../site/online/docs/_static/
cp build/html/_static/*.png ../site/online/docs/_static/
cp build/html/examples/*.html ../site/online/docs/examples/

echo "Done!"
