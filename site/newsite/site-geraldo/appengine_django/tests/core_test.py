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

"""Tests that the core module functionality is present and functioning."""


import unittest

from appengine_django import appid
from appengine_django import have_appserver


class AppengineDjangoTest(unittest.TestCase):
  """Tests that the helper module has been correctly installed."""

  def testAppidProvided(self):
    """Tests that application ID and configuration has been loaded."""
    self.assert_(appid is not None)

  def testAppserverDetection(self):
    """Tests that the appserver detection flag is present and correct."""
    # It seems highly unlikely that these tests would ever be run from within
    # an appserver.
    self.assertEqual(have_appserver, False)
