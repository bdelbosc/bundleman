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

$Id: test_productman.py 38359 2006-08-23 12:38:41Z bdelbosc $
"""
import sys
import os
import unittest
import logging

from svnsandbox import SvnSandBox

def fixIncludePath():
    """Add .. to the path"""
    module_path = os.path.join(os.path.dirname(__file__), "..")
    sys.path.insert(0, os.path.normpath(module_path))
fixIncludePath()

from bundleman.utils import command, initLogger
from bundleman.productman import ProductMan
from bundleman.bundleman import BundleMan

logger = logging.getLogger('bm.test_bundleman')
initLogger('/tmp/bm-tests.log', True)

class BMBundleMan(unittest.TestCase):
    """unit test."""

    def test_bundleman(self):
        name = 'app'
        products = ('foo', 'bar')
        svn = SvnSandBox()
        url, products_url = svn.createBundle(name, products)

        path = svn.coBundle(name)
        # init products
        for product in products:
            pman = ProductMan(os.path.join(path, product), force=True)
            pman.init()

        # release 1
        release_tag1 = name.upper()+'rc1'
        release_tag2 = name.upper()+'rc2'
        release_tag3 = name.upper()

        bman = BundleMan(path, release_tag1)
        bman.doAction()
        bman.buildArchive(svn.coroot)

        # branch to patch release 1
        bman.analyze(force=True)
        branch_url = bman.branch()

        # co
        branch_path = os.path.join(svn.coroot, release_tag1+'-branch')
        command('svn co %s %s' % (branch_url, branch_path))

        # change something
        prod_branch_path = os.path.join(branch_path, products[0])
        changes = os.path.join(prod_branch_path, 'CHANGES')
        f = open(changes, 'w+')
        f.write(pman.tpl_changes % 'branch changes')
        f.close()
        command('svn commit -m"change" %s' % changes)
        command('svn up %s' % branch_path)

        # release 2
        bman = BundleMan(branch_path, release_tag2)
        bman.doAction()


        # branch to patch release 2
        bman.analyze(force=True)
        branch_url = bman.branch()

        # co
        branch_path = os.path.join(svn.coroot, release_tag2+'-branch')
        command('svn co %s %s' % (branch_url, branch_path))

        # change something
        prod_branch_path = os.path.join(branch_path, products[0])
        changes = os.path.join(prod_branch_path, 'CHANGES')
        f = open(changes, 'w+')
        f.write(pman.tpl_changes % 'branch changes')
        f.close()
        command('svn commit -m"change" %s' % changes)
        command('svn up %s' % branch_path)

        # release 3
        bman = BundleMan(branch_path, release_tag3)
        bman.doAction()
        bman.addChangelog(release_tag1, release_tag3)
        bman.buildArchive(svn.coroot)


def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BMBundleMan))
    return suite

if __name__ == '__main__':
    unittest.main()
