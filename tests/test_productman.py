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
"""Test the productman

$Id: test_productman.py 49118 2006-09-14 09:32:01Z bdelbosc $
"""
import sys
import os
import unittest
from svnsandbox import SvnSandBox
import logging

def fixIncludePath():
    """Add .. to the path"""
    module_path = os.path.join(os.path.dirname(__file__), "..")
    sys.path.insert(0, os.path.normpath(module_path))
fixIncludePath()

from bundleman.utils import command, initLogger
from bundleman.productman import ProductMan

logger = logging.getLogger('bm.test_productman')
initLogger('/tmp/bm-tests.log', True)

class BMProductMan(unittest.TestCase):
    """unit test."""

    def test_productman(self):
        name = 'foo'
        svn = SvnSandBox()
        url = svn.createProduct(name)
        path = svn.coProduct(name)
        pman = ProductMan(path, force=True)
        pman.analyze()
        self.assert_(pman.url, url)

        # init product version 0.0.0
        pman.init()

        pman.analyze()
        self.assert_(os.path.exists(os.path.join(path, 'VERSION')))
        self.assert_(os.path.exists(os.path.join(path, 'HISTORY')))
        self.assert_(os.path.exists(os.path.join(path, 'CHANGES')))
        self.assertEquals(pman.status, 'new_version')

        # package product the first package is 0.1.0
        pman.doAction()

        pman.analyze()
        self.assertEquals(pman.status, 'use_tag')
        self.assertEquals(pman.version, [name, '0.1.0', '1'])

        rev_0_1_0 = pman.revision

        # changes something
        file_name = os.path.join(path, 'foo')
        f = open(file_name, 'w+')
        f.write('touch\n')
        f.close()

        # non svn versioned file doesn't change status whatever force mode is
        pman.analyze(force=True)
        self.assertEquals(pman.status, 'use_tag')
        force_bak = pman.force
        pman.force = False
        self.assertEquals(pman.getStatus(), 'use_tag')
        pman.force = force_bak

        command('svn add %s' % file_name)
        command('svn commit -m"add file" %s' % file_name)

        pman.analyze(force=True)
        self.assertEquals(pman.status, 'svn_not_uptodate')

        command('svn up %s' % path)
        pman.analyze(force=True)
        self.assertEquals(pman.status, 'missing_changes')

        # in force mode, local modifications of svn versioned files are ok
        # in non force mode, user has to check in before packaging
        f = open(file_name, 'w+')
        f.write('new touch\n')
        f.close()
        pman.analyze(force=True)
        self.assertEquals(pman.status, 'missing_changes')
        force_bak = pman.force
        pman.force = False
        self.assertEquals(pman.getStatus(), 'svn_not_uptodate')
        pman.force = force_bak
        # reverting local modifications
        command('svn revert %s' % file_name)


        # jump in the past back to rev_0_1_0
        command('svn up -r%s %s' % (rev_0_1_0, path))
        # the wc is not up to date with the svn repo
        pman.analyze(force=True)
        self.assertEquals(pman.revision, rev_0_1_0)
        self.assertEquals(pman.status, 'svn_not_uptodate')
        # back to the present
        command('svn up %s' % path)


        changes = os.path.join(path, 'CHANGES')
        f = open(changes, 'w+')
        f.write(pman.tpl_changes % 'something change')
        f.close()
        command('svn commit -m"update" %s' % changes)
        command('svn up %s' % path)

        pman.analyze(force=True)
        self.assertEquals(pman.status, 'new_version')
        self.assertEquals(pman.version_new[1], '0.2.0')

        # package
        pman.doAction()
        self.assertEquals(pman.status, 'use_tag')
        self.assertEquals(pman.version[1], '0.2.0')

        # package twice should not do anything
        pman.analyze(force=True)
        pman.doAction()
        self.assertEquals(pman.version[1], '0.2.0')

        # create a branch
        branch_name = 'user-refactor'
        branch_url = url.replace('/trunk', '/branches/' + branch_name)
        branch_path = path + '-' + branch_name
        command('svn cp -m"create a branch" %s %s' % (url, branch_url))
        command('svn co %s %s' % (branch_url, branch_path))

        pman = ProductMan(branch_path)
        pman.analyze()

        self.assert_(pman.url, branch_url)
        self.assertEquals(pman.status, 'use_tag')

        # change something
        changes = os.path.join(branch_path, 'CHANGES')
        f = open(changes, 'w+')
        f.write(pman.tpl_changes % 'branch changes')
        f.close()
        command('svn commit -m"change" %s' % changes)
        command('svn up %s' % branch_path)

        # package
        pman.analyze(force=True)
        pman.doAction()
        self.assertEquals(pman.status, 'use_tag')
        self.assertEquals(pman.version[1], '0.3.0-user-refactor')


def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BMProductMan))
    return suite

if __name__ == '__main__':
    unittest.main()
