#!/usr/bin/env bash
rm -rf `find . -name "*.pyc"`
mv site-geraldo/local_settings.py site-geraldo/_local_settings.py

#appcfg.py update site-geraldo/

#mv site-geraldo/_local_settings.py site-geraldo/local_settings.py

