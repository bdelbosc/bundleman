#! /usr/bin/env python
# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
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
"""Bundle Manager setup

$Id: setup.py 49829 2006-10-24 16:34:17Z bdelbosc $
"""
from distutils.core import setup

from bundleman.version import __version__
from tests.distutilstestcommand import TestCommand

setup(
    name="bundleman",
    version=__version__,
    description="Manage svn bundle releasing.",
    long_description="""\
BundleMan try to manage releasing of application built on versioned products
under subversion.

An application is seen as a products suite defined using subversion
svn:externals property. An application is a bundle of products. Products are
versioned piece of software.

Releasing an application is about taking care of tagging the source
repository, managing version of each products, managing CHANGELOGs, creating
a source package archive, giving ways to maitain a release without blocking
the trunk development.


Main features:

* BundleMan is free software distributed under the GNU GPL.

* It uses a recommended trunk/branches/tags repository layouts for
  products and bundles.

* It uses standard versioning MAJOR.MINOR.BUGFIX-RELEASE for products.

* Versioning of products is done automaticly by analysing a CHANGES file.

* Enforce CHANGELOG quality by requiring a product CHANGES file.

* It generates an application CHANGELOG.

* There is no locking of the trunk or version's conflict when patching a
  released application.

* Can manage public, private or remote products.

* BundleMan is written in python and can be easily customized.

""",
    author="Benoit Delbosc",
    author_email="bdelbosc@nuxeo.com",
    url="http://public.dev.nuxeo.com/~ben/bundleman/",
    download_url="http://public.dev.nuxeo.com/~ben/bundleman/bundleman-%s.tar.gz"%__version__,
    license='GPL',
    packages=['bundleman'],
    package_dir={'bundleman': 'bundleman'},
    scripts=['scripts/bm-bundle',
             'scripts/bm-product',
             ],
    keywords='packaging releasing bundle subversion versioning',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: System :: Software Distribution',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Version Control',
        'Topic :: System :: Archiving :: Packaging',
    ],
    cmdclass = { 'test': TestCommand,}
)
