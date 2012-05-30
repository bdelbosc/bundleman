# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
"""Test the make_release

$Id: test_utils.py 49721 2006-10-18 08:08:27Z bdelbosc $
"""
import sys
import os
import unittest
import doctest
import logging

def fixIncludePath():
    """Add .. to the path"""
    module_path = os.path.join(os.path.dirname(__file__), "..")
    sys.path.insert(0, os.path.normpath(module_path))
fixIncludePath()

import bundleman
from bundleman.utils import parseZopeVersionFile, parseNuxeoChanges
from bundleman.utils import parseNuxeoVersionFile, parseVersionString
from bundleman.utils import isSvnCompatible, initLogger

logger = logging.getLogger('bm.test_productman')
initLogger('/tmp/bm-tests.log', True)

class BMUtils(unittest.TestCase):
    """unit test."""

    def test_parseZopeVersionFile(self):
        samples = {'Foo-1.2.3-4': ['Foo', '1.2.3', '4'],
                   'Foo 1.2.3-4': ['Foo', '1.2.3', '4'],
                   'Foo 1.2.3': ['Foo', '1.2.3', '1'],
                   'Foo 1.2-3': ['Foo', '1.2', '3'],
                   'Foo 2-3': ['Foo', '2', '3'],
                   '1.2.3-4': [None, '1.2.3', '4'],
                   '1.2.3-4': [None, '1.2.3', '4'],
                   '1.2.3': [None, '1.2.3', '1'],
                   '1.2-3': [None, '1.2', '3'],
                   '12': [None, '12', '1'],
                   'Foo-bar 14.23.1234-12': ['Foo-bar', '14.23.1234', '12'],
                   'Foo2-1.2-3': ['Foo2', '1.2', '3'],
                   'Foo-0.4.0-Foo-3_0-branch-1':
                   ['Foo-Foo-3_0-branch', '0.4.0', '1'],
                   '0.3.1-Foo-3_0-branch-3': ['Foo-3_0-branch', '0.3.1', '3'],
                   'CMF-1.5.0': [None, '1.5.0', '1'],
                   }
        for txt, expected in samples.items():
            res = parseZopeVersionFile(txt)
            self.assertEquals(res, expected)

    def test_parseVersionString(self):
        samples = {'1.3': [1, 3, 0, ''],
                   '1.3.2': [1, 3, 2, ''],
                   '1.3.2-user-refactor': [1, 3, 2, 'user-refactor'],
                   }
        for txt, expected in samples.items():
            res = parseVersionString(txt)
            self.assertEquals(res, expected)

    def test_parseNuxeoChanges(self):
        content = """Requires:
~~~~~~~~~
-
New features:
~~~~~~~~~~~~~
-
Bug fixes:
~~~~~~~~~~
-
New internal features:
~~~~~~~~~~~~~~~~~~~~~~
-"""
        self.assertEquals(parseNuxeoChanges(content), ([], [], [], []))
        content = """Requires:
~~~~~~~~~
-
New features:
~~~~~~~~~~~~~
- foo
  bar
Bug fixes:
~~~~~~~~~~
- bar
New internal features:
~~~~~~~~~~~~~~~~~~~~~~
-
-"""
        self.assertEquals(parseNuxeoChanges(content), ([], ['- foo', '  bar'],
                                                       ['- bar'], []))
        content = """Requires:
~~~~~~~~~
-
New features:
~~~~~~~~~~~~~
-
Bug fixes:
~~~~~~~~~~
-
New internal features:
~~~~~~~~~~~~~~~~~~~~~~
- foo
"""
        self.assertEquals(parseNuxeoChanges(content), ([], [],
                                                       [], ['- foo']))


    def test_parseNuxeoVersionFile(self):
        content = """# NUXEO PRODUCT CONFIGURATION FILE
# do not edit this file
PKG_NAME=CPSCore
PKG_VERSION=3.32.0-user-branch
PKG_RELEASE=2
"""
        self.assertEquals(parseNuxeoVersionFile(content),
                          ['CPSCore', '3.32.0-user-branch', '2'])
        content = """# NUXEO PRODUCT CONFIGURATION FILE
# do not edit this file
PKG_NAME=CPSCore
PKG_VERSION=3.32.0
PKG_RELEASE=1
"""
        self.assertEquals(parseNuxeoVersionFile(content),
                          ['CPSCore', '3.32.0', '1'])
    def test_svnCompatible(self):
        minimum = '1.2'
        self.assert_(isSvnCompatible(minimum), 'Sorry bundleman requires '
                     'Subversion >= %s' % minimum)

def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BMUtils))
    suite.addTest(doctest.DocTestSuite(bundleman.utils))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())