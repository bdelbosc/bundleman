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
"""Create a svn tree

$Id: svnsandbox.py 49097 2006-08-25 10:28:21Z bdelbosc $
"""
import sys
import os
import unittest
from tempfile import mkdtemp
import logging

def fixIncludePath():
    """Add .. to the path"""
    module_path = os.path.join(os.path.dirname(__file__), "..")
    sys.path.insert(0, os.path.normpath(module_path))
fixIncludePath()

from bundleman.utils import command, initLogger, SVN_EXTERNALS
from bundleman.productman import ProductMan

logger = logging.getLogger('bm.test_svnsandbox')
initLogger('/tmp/bm-tests.log', True)

class SvnSandBox:
    """A svn sandbox.

    bundles
        foo
            trunk
            tags
            branches
        ...
    products
        bar
            trunk
            tag
            branches
        ...
    """

    def __init__(self):
        root = mkdtemp(prefix="bm-")
        logger.info('SvnSandBox root: %s' % root)
        self.root = root
        self.coroot = os.path.join(root, 'co')
        os.mkdir(self.coroot)
        os.mkdir(os.path.join(root, 'tmp'))
        svnroot = os.path.join(root, 'svn')
        command('svnadmin create %s' % svnroot)
        svnroot = 'file://' + svnroot
        self.svnroot = svnroot
        command('svn mkdir -m"create" %s/bundles' % svnroot)
        command('svn mkdir -m"create"  %s/products' % svnroot)

    def createProduct(self, product):
        """Create a product tree."""
        product_url = '%s/products/%s' % (self.svnroot, product)
        logger.info('createProduct %s' % product_url)
        command('svn mkdir -m"create" %s %s/trunk %s/tags %s/branches' % (
            product_url, product_url, product_url, product_url))
        return product_url + '/trunk'

    def createBundle(self, bundle, products):
        """Create a bundle with products."""
        svnroot = self.svnroot
        bundle_url = '%s/bundles/%s' % (svnroot, bundle)
        logger.info('createBundle %s' % bundle_url)
        command('svn mkdir -m"create" %s %s/trunk %s/tags %s/branches' % (
            bundle_url, bundle_url, bundle_url, bundle_url))
        bundle_url = bundle_url + '/trunk'
        bundle_path = self.coBundle(bundle)

        externals = os.path.join(bundle_path, SVN_EXTERNALS)
        f = open(externals, 'w+')
        products_url = []
        for product in products:
            product_url = self.createProduct(product)
            products_url.append(product_url)
            f.write('%s %s\n' % (product, product_url))
        f.close()
        command('svn ps svn:externals -F %s %s' % (externals, bundle_path))
        command('svn add %s' % externals)
        command('svn commit -m"setup externals" %s' % bundle_path)
        command('svn up %s' % bundle_path)
        return bundle_url, products_url

    def coBundle(self, bundle, tag='trunk'):
        """Check out a bundle."""
        bundle_path = '%s/%s' % (self.coroot, bundle)
        command('svn co %s/bundles/%s/%s %s' % (self.svnroot, bundle, tag,
                                                bundle_path))
        return bundle_path

    def coProduct(self, product, tag='trunk'):
        """Check out a product."""
        product_path = '%s/%s' % (self.coroot, product)
        command('svn co %s/products/%s/%s %s' % (self.svnroot, product, tag,
                                                 product_path))
        return product_path

    def upProduct(self, product_path):
        """Svn up a product path."""
        command('svn up %s' % product_path)


class SvnSandBoxTestCase(unittest.TestCase):
    """unit test."""
    def setUp(self):
        self.svn = SvnSandBox()

    def test_createProduct(self):
        svn = self.svn
        svn.createProduct('foo')

    def test_createBundle(self):
        svn = self.svn
        svn.createBundle('bundle-foo', ['prod-foo', 'prod-bar'])


def test_suite():
    """Return a test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SvnSandBoxTestCase))
    return suite

if __name__ == '__main__':
    unittest.main()
