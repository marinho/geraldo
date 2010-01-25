#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys

from appengine_django.db.base import destroy_datastore
from appengine_django.db.base import get_test_datastore_paths

from django.core.management.base import BaseCommand


class Command(BaseCommand):
  """Overrides the default Django testserver command.

  Instead of starting the default Django development server this command fires
  up a copy of the full fledged appengine dev_appserver.

  The appserver is always initialised with a blank datastore with the specified
  fixtures loaded into it.
  """
  help = 'Runs the development server with data from the given fixtures.'

  def run_from_argv(self, argv):
    fixtures = argv[2:]

    # Ensure an on-disk test datastore is used.
    from django.db import connection
    connection.use_test_datastore = True
    connection.test_datastore_inmemory = False

    # Flush any existing test datastore.
    connection.flush()

    # Load the fixtures.
    from django.core.management import call_command
    call_command('loaddata', 'initial_data')
    if fixtures:
      call_command('loaddata', *fixtures)

    # Build new arguments for dev_appserver.
    datastore_path, history_path = get_test_datastore_paths(False)
    new_args = argv[0:1]
    new_args.extend(['--datastore_path', datastore_path])
    new_args.extend(['--history_path', history_path])
    new_args.extend([os.getcwdu()])

    # Add email settings
    from django.conf import settings
    new_args.extend(['--smtp_host', settings.EMAIL_HOST,
                     '--smtp_port', str(settings.EMAIL_PORT),
                     '--smtp_user', settings.EMAIL_HOST_USER,
                     '--smtp_password', settings.EMAIL_HOST_PASSWORD])

    # Start the test dev_appserver.
    from google.appengine.tools import dev_appserver_main
    dev_appserver_main.main(new_args)
