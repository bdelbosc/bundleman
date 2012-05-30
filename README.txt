=========
BundleMan
=========

:author: Benoit Delbosc

:address: bdelbosc _at_ nuxeo.com

:version: BundleMan/1.3.0

:revision: $Id: README.txt 53582 2009-03-26 19:52:05Z bdelbosc $

:Copyright: (C) Copyright 2006 Nuxeo SAS (http://nuxeo.com).
            This program is free software; you can redistribute it and/or
            modify it under the terms of the GNU General Public License as
            published by the Free Software Foundation; either version 2 of
            the License, or (at your option) any later version.
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
            General Public License for more details.
            You should have received a copy of the GNU General Public
            License along with this program; if not, write to the Free
            Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
            MA 02111-1307, USA.

:abstract: This document describes the usage of the BundleMan_ tool. This tool
    enables to release application with versioned products using subversion.

.. sectnum::    :depth: 1

.. contents:: Table of Contents


Introducing BundleMan
=====================

What is BundleMan ?
-------------------

BundleMan manages the release of applications built on versioned
products under subversion_ (aka versioned multi modules).

An application is seen as a products suite defined using subversion_
`svn:externals`_ property. An application is a bundle of products.
Products are versioned pieces of software.

Releasing an application is about taking care of tagging the source
repository, managing version of each products, managing CHANGELOG, creating
a source package archive, giving ways to maitain a release without blocking
the trunk development.


Main features:

* BundleMan is free software distributed under the `GNU GPL`_.

* It uses a recommended `trunk/branches/tags`_ repository layouts for
  products and bundles.

* It uses standard versioning MAJOR.MINOR.BUGFIX-RELEASE for products.

* Versioning of products is done automaticly by analysing a CHANGES file.

* Enforce CHANGELOG quality by requiring a product CHANGES file.

* It Generates an application CHANGELOG.

* There is no locking of the trunk or version's conflict when patching a
  released application.

* Can manage public, private or remote products.

* BundleMan is written in python and can be easily customized.


Where to find BundleMan ?
-------------------------

Get the latest package from python `Cheese Shop`_.

Or use the bleeding edge ::

   svn co http://svn.nuxeo.org/pub/tools/bundleman/trunk bundleman


Installation
------------

See the INSTALL_ file for requirement and installation.


Examples
--------

You can play with BundleMan in a sandbox using the unit test environment.

From the extracted archive::

     $ python setup.py test
     running test
     ...
     INFO: Archive: /tmp/bm-jE9JMJ/co/APP.tgz
     ...
     Ran 6 tests in 72.976s
     OK

Look at the temporary folder ``/tmp/bm-{WhAtEvEr}/`` you will find a ``svn``
folder which contains the svn sandbox repository and a ``co`` folder with
working copies of an application. For example ``co/app`` is a trunk
bundle with 2 empty products ``foo`` and ``bar``. You can test some `bm-bundle`
commands from here, try ``bm-bundle -v`` then try to release this apps
following the use case below.



Documentation
-------------

This page is the main BundleMan_ documentation, there are also:

* CHANGES_ for information about distribution contents.
* INSTALL_ for requirement and installation.
* API_ documentation generated with epydoc_.


Use cases
=========

Inititialize an application to use BundleMan
--------------------------------------------

* Create svn `trunk/branches/tags`_ repository layouts for bundles and
  products::

    somewhere/bundles
      AppA
        trunk       dev bundle with svn:externals that point to products
        branches    branches created to patch a released application
        tags        released application
      ...
    somewhere-else/products
      ProdA
        trunk
        branches
        tags
      ProdB
        trunk
        branches
        tags
      ...

* See `svn:externals`_ to setup/configure your bundle.

* BundleMan intialize

  - Checkout your bundle::

      svn co somewhere/bundles/AppA/trunk AppA

  - Initialize all products that you want to manage with BundleMan, products
    must be in a trunk or branch. Go into the product directory and
    run a::

      bm-product --init

    This will add a CHANGES, VERSION and HISTORY files to the product and
    add a svn property named bundleman.

  - Initialize the bundle from the bundle working copy by running::

      bm-bundle --init

    It will create a `svn-externals` file that contains the svn externals
    definition.


Working on an application
-------------------------

* Changing bundle definition.

  You should edit the `svn-externals` file to update your bundle definition,
  then ::

      svn ps svn:externals -F svn-externals .
      svn commit -m"udpate the bundle definition" -N svn-externals .

  The `svn-externals` file is usefull to have readable `svn:externals` diff
  and to look at the bundle contents from a trac. Be sure that all
  developpers use this file to edit the bundle definition.

* Working on a product.

  When working on a product sources, in addition to your commit message, you
  will have to fill a CHANGES file.

  The content of this file is the changes between the current dev and the
  last product release.

  This file contains 4 sections:

      - Requires: things that must be done to use or install this new release.

      - New features: list of new features, customer oriented.

      - Bug fixes: list of bug fix.

      - New internal features: list of new features, devel oriented.

  CHANGES exemple::

       Requires
       ~~~~~~~~
       - ProdC > 1.2.3
       New features
       ~~~~~~~~~~~~
       - Enable customer ...
       Bug fixes
       ~~~~~~~~~
       - fix #1234: Site error when...
       New internal features
       ~~~~~~~~~~~~~~~~~~~~~
       - API Changes ...


  Depending on the CHANGES content BundleMan will compute the new version of
  the product.

  When releasing, BundleMan will ask you to fill this file if it is empty while
  you have commited sources since the last product release.

  This file is reseted during product release and flush into an HISTORY file.

  The HISTORY file is turn into a CHANGELOG.txt file in the release archive.

  Product CHANGELOG.txt exemple::

    ===========================================================
    Package: ProdA 3.2.0
    ===========================================================
    First release built by: ben at: 2006-09-19T08:03:54
    SVN Tag: path/to/products/ProdA/tags/3.2.0
    Build from: path/to/products/ProdA/trunk@1234

    Requires
    ~~~~~~~~
    - ProdC > 1.2.3
    New features
    ~~~~~~~~~~~~
    - Enable customer ...
    Bug fixes
    ~~~~~~~~~
    - fix #1234: Site error when ...
    New internal features
    ~~~~~~~~~~~~~~~~~~~~~
    - API Changes ...

    ===========================================================
    Package: ProdA 3.1.0
    ===========================================================
    First release built by: ben at: 2006-09-17T18:03:41
    SVN Tag: path/to/products/ProdA/tags/3.1.0
    Build from: path/to/products/ProdA/trunk@1123

    Requires
    ~~~~~~~~
    ....



Releasing an application
------------------------

On a working copy of the trunk bundle

* Check the status of your working copy::

    $ bm-bundle
    INFO: List of actions to do:
    ProdA                   3.2.0-1             Requires a svn update/commit.
    ProdB                   1.0.0-1             New version: 1.1.0-1
    ProdC                   2.0.0-1             CHANGES file must be filled !.
    WARNING: Bundle not ready to be released.

  Running `bm-bundle` without option is purely introspective.


* Depending on the status you may need to fill product's CHANGES file,
  commit locally modified or svn update products.
  Re run bm-bundle until the status is 'Ready'::

    $ bm-bundle
    INFO: List of actions to do:
    ProdB                   1.0.0-1             New version: 1.1.0-1
    ProdC                   2.0.0-1             Nex version: 2.0.1-1
    INFO: Ready:  Going to release some products.

* Release the application::

     $ bm-bundle --release=APPA-2006-rc1
     INFO: Analyze all products ...
     INFO: Tag product ProdB version 1.1.0-1
     INFO: Tag path/to/products/ProdB/tags/1.1.0 done.
     ....
     INFO: Create a bundle tag APPA-2006-rc1
     INFO: Analyze all products ...
     INFO: Creating bundle path/to/bundles/AppA/tags/APPA-2006-rc1

  Note that in addition to the new bundle tags, it created releases for
  ProdB and ProdC products.

* Create a CHANGELOG of the application since the previous release APPA-2005::

     $ bm-bundle --changelog APPA-2005:APPA-2006-rc1 > CHANGELOG.txt

  You can edit, add and commit this file to the APPA-2006-rc1 tag.

* Create a tarball archive::

     $ bm-bundle --archive APPA-2006-rc1 -o /tmp/
     INFO: Analyze all products ...
     INFO: Creating archive: APPA-2006-rc1.tgz
     INFO: Archive: /tmp/APPA-2006-rc1.tgz

  In this archive you will have a `version.txt` for the bundle (with
  'APPA-2006-rc1' content) and for each products.


Patching a release
------------------

You want to patch the APPA-2006-rc1 to release the rc2.

From a working copy of he trunk bundle

* Create a bundle branch::

     $ bm-bundle --branch=APPA-2006-rc1
     INFO: Branching path/to/bundles/app/tags/APPA-2006-rc1 -> path/to/bundles/app/branches/APPA-2006-rc1 hash_tag: rel1058079549.
     INFO: Creating bundle path/to/bundles/AppA/branches/APPA-2006-rc1

  This will create a branch for each versioned products and create a new
  bundle in `bundles/AppA/branches`.

  Note that the product branch is created using a hash of the RELEASE_TAG
  because it hides the RELEASE_TAG in the case of a private bundle that uses
  public products. This means that you will not have 'MYSECRETPROJECTrc1'
  tag in a a product that is on a public svn.

* Either switch to the branch::

     svn switch path/to/bundles/app/branches/APPA-2006-rc1

  or checkout the new bundle branch::

    svn co path/to/bundles/app/branches/APPA-2006-rc1

* Commit the fixes and update CHANGES in the different products

* Release:

   - Check the status::

       $ bm-bundle
       INFO: List of actions to do:
       ProdA          3.2.1-1              New version: 3.2.2-rel1058079549-1
       INFO: Ready: Going to release some products.

   - Depending on the status you may need to fill product's CHANGES file,
     commit locally modified or svn update products.

   - Release::

         $ bm-bundle --release APPA-2006-rc2
         INFO: Analyze all products ...
         INFO: Tag product ProdA version 3.2.2-rel1058079549-1
         INFO: Tag path/to/products/foo/tags/3.2.2-rel1058079549 done.
         ProdB                       1.1.0-1              Already released.
         ProdC                       2.0.1-1              Already released.
         INFO: Create a bundle tag APPA-2006-rc2
         INFO: Analyze all products ...
         INFO: Creating bundle path/to/bundles/AppA/tags/APPA-2006-rc2

    Note that ProdA is released with the version 3.2.2-rel1058079549-1, the
    release tag may change for a same target release like (APPA-2006-beta,
    APPA-2006-rc1 ...rc2 and final), using a hash we will not have a weird
    APPA-2006-rc1 tag in the final APPA-2006 bundle.

* You can keep this branch to patch APPA-2006-rc2 and create the final
  APPA-2006.

* Merge your patch to the trunk: `bm-bundle --merge=APPA-2006-rc2`
  This will merge all products from bundle/App/tags/APPA-2006-rc2 to products
  in the bundle/AppA/trunk and switch to trunk.

  **NOT YET IMPLEMENTED**

* Fix eventual conflict then commit.

That's all.


Product release
---------------

You can release a single product using `bm-product --release`

Mutliple release
----------------

You can release an AppB that shares products with AppA without any version
conflit.


Verifying a package installation
--------------------------------

When creating an archive BundleMan adds a MD5SUMS file, so you can check that
a tarball installation is valid::

  cd path/to/app
  md5sum -c MD5SUMS && echo "Package verified successfully"

*Note that md5sum will not complain about new files.*


BundleMan commands
==================

There is only 2 commands provided by BundleMan, bm-product to manage a product
and bm-bundle to manage the bundle (ie the application).

Default operation without options are purely introspective, zero risk.

To check what BundleMan is doing you can use the debug option `--debug` or
look into the log file `/tmp/bundleman.log`.



bm-product
----------

Usage
~~~~~
::

    bm-product [options] [WCPATH]

    bm-product is a product release manager. See BundleMan documentation for more
    information.

    WCPATH is a svn working copy of a product.

    Product follows the classic trunk/tags/branches svn tree.

    Product is versioned using 3 files:

    * CHANGES (not present in an archive) this file contains 4 sections:
      - Requires: things that must be done to install this new release.
      - New features: list of new features customer oriented.
      - Bug fixes: list of bug fix.
      - New internal features: list of new features devel oriented.
      This file *MUST* be filled during devel of the product.
      This file is reseted during product release.

    * VERSION: (or version.txt in an archive) this file contains the product name,
      product version and release number. The version format is
      MAJOR.MINOR.BUGFIX[-branch_name].

      A new version is automaticly computed using the content of the CHANGES file
      with the following rules:

       - If there is *ONLY* bug fixes increment the BUGFIX number else increment the
         MINOR number.

       - If the svn url is a branch append the branch name to the version.

    * HISTORY (or CHANGELOG.txt in an archive)
      This file contains the concatenation of all CHANGES.

Exemples
~~~~~~~~
::

      bm-product
                    Display status and action to be done for WCPATH.

      bm-product --init
                    Initialize the WCPATH product:
                    * Check that the WCPATH point to a trunk svn url.
                    * Check that tags and branches svn url exists.
                    * If missing prompt the user to add VERSION, CHANGES
                    and HISTORY files to the product working copy and
                    commit them.

      bm-product --release
                   Release the WCPATH product:
                   * Analyse the working copy:

                      - Checks that WCPATH is up to date with the svn.
                      - Parses the CHANGES file and computes the new version
                      - If CHANGES is empty checks the that there is no diff
                        between the WCPATH and the tagged version.

                   * Create a tag using WCPATH svn revision: tags/VERSION
                   * Fush CHANGES into HISTORY, update VERSION files and commit,
                     in the tag and the WCPATH url.

      bm-product --archive -o /tmp
                   Create a tarball archive in the /tmp directory. The product must
                   be released. The tarball contains a MD5SUMS file and can be
                   verified using `md5sum -c MD5SUMS`.


Options
~~~~~~~
::

    --version               show program's version number and exit
    --help, -h              show this help message and exit
    --status, -s            Show status and action to be done for WCPATH.
    --init                  Initialize the WCPATH product.
    --release               Release the product WCPATH.
    --major                 Increment the MAJOR number instead of the MINOR number
                            of the version.
    --again                 Rebuild the same version, increment the release
                            number.
    --archive, -a           Build a targz archive.
    --output-directory=OUTPUT_DIR, -o OUTPUT_DIR
                            Directory to store the archive.
    --force, -f             No prompt during --init. Replaces an existing tag
                            during --release. Release even with locally modified
                            files.
    --verbose, -v           Verbose output
    --debug, -d             Debug output


bm-bundle
---------


Usage
~~~~~
::

  bm-bundle [options] [WCPATH]

  bm-bundle is a bundle release manager. See BundleMan documentation for
  more information.

  WCPATH is a svn working copy path of a bundle, using current path if not
  specified.

  A bundle is an suite of products, this suites is defined using
  svn:externals property of the bundle folder.

  A bundle follows the classic trunk/tags/branches svn tree.

  Products may be versionned using bm-product tool.

Examples
~~~~~~~~
::

  bm-bundle
                        Display status and action to be done.

  bm-bundle --init
                        Initialize WCPATH bundle by adding svn-externals
                        file to trunk

  bm-bundle --release APPrc1
                        Create release bundle in tags/APPrc1 that point to
                        released products.

  bm-bundle --release APPrc1 -a
                        Create a release and a targz archive in one step.

  bm-bundle --archive APPrc1 -o /tmp
                        Create a targz archive in /tmp directory.
                        The tarball contains a MD5SUMS file and can be
                        verified using `md5sum -c MD5SUMS`.

  bm-bundle --archive APPrc1 --archive-root-directory Products
                        Create a targz archive of APPrc1 release with a root
                        folder named Products.

  bm-bundle --branch APPrc1
                        Create a branch bundle in branch/APPrc1 that point to
                        branched products.
                        A product branch will be created for each versioned
                        products. The branch name use a hash(APPrc1) key.

  bm-bundle --changelog APPrc1:APPrc2
                        Output a global bundle changelog between bundle tags.

  bm-bundle --release APPrc2 --changelog APPrc1: -a -o /tmp --scp bar:/tmp
                        Create a release with a global changelog, build
                        the targz archive, scp it to bar:/tmp in one step.


Options
~~~~~~~
::

  --version               show program's version number and exit
  --help, -h              show this help message and exit
  --status, -s            Show action to be done.
  --init, -i              Initialize the bundle working copy.
  --release=RELEASE_TAG   Release the bundle.
  -a                      Build a tar gz archive, must be used with --release
                          option.
  --archive=RELEASE_TAG   Build a tar gz archive from an existing RELEASE_TAG.
  --archive-root-directory=ARCHIVE_ROOT
                          The name of the root directory in the archive, default
                          is RELEASE_TAG.
  --output-directory=OUTPUT_DIR, -o OUTPUT_DIR
                          Directory to store the archive.
  --scp=REMOTE_PATH       scp the archive to a REMOTE_PATH.
  --branch=RELEASE_TAG    Branch the bundle release.
  --changelog=TAG1:TAG2   Output a changelog between 2 bundle tags. If TAG2 is
                          missing it uses the RELEASE_TAG.
  --changelog-url=TAG1_URL:TAG2_URL
                          Output a changelog between 2 bundle url tags.
  --force, -f             No prompt during --init.
  --log-file=LOG_FILE, -l LOG_FILE
                          The log file path. Default is ~/bundleman.log.
  --verbose, -v           Verbose output
  --debug, -d             Debug output


.. _INSTALL: INSTALL.html
.. _CHANGES: CHANGES.html
.. _API: api/index.html
.. _BundleMan: http://public.dev.nuxeo.com/~ben/bundleman/
.. _epydoc: http://epydoc.sourceforge.net/
.. _`Cheese Shop`: http://www.python.org/pypi/bundleman/
.. _`svn:externals`: http://svnbook.red-bean.com/en/1.2/svn.advanced.externals.html
.. _subversion: http://subversion.tigris.org/
.. _`trunk/branches/tags`: http://svnbook.red-bean.com/en/1.2/svn.branchmerge.maint.html#svn.branchmerge.maint.layout
.. _`GNU GPL`: http://www.gnu.org/licenses/licenses.html


.. Local Variables:
.. mode: rst
.. End:
.. vim: set filetype=rst:
