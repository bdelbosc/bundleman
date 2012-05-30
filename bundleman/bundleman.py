# (C) Copyright 2006-2008 Nuxeo SAS <http://nuxeo.com>
# Authors:
# bdelbosc@nuxeo.com
# M.-A. Darche
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
"""Bundle Manager

$Id: bundleman.py 53209 2008-12-01 09:55:43Z madarche $
"""
import sys
import os
import logging
from tempfile import mkdtemp, NamedTemporaryFile
from optparse import OptionParser, TitledHelpFormatter

from version import __version__
from utils import command, initLogger, computeTagUrl, createBundle, getHashTag
from utils import SVN_EXTERNALS, parseNuxeoHistory, rst_title
from utils import prepareProductArchive, computeBundleTagUrl
from productman import ProductMan


logger = logging.getLogger('bm.bundleman')


def isValidBundlePath(bundle_path):
    """Check that the bundle_path is valid."""
    if not bundle_path:
        return False
    if not os.path.exists(os.path.join(bundle_path, '.svn')):
        return False
    ret, output = command('svn pl %s | grep "svn:externals"' % bundle_path,
                          do_raise=False)
    if ret:
        return False
    if len(output) != 1:
        return False
    return True


class BundleMan:
    """A Bundle manager class."""
    def __init__(self, bundle_path, release_tag=None, verbose=False,
                 force=False, requires_valid_bundle=True):
        self.bundle_path = bundle_path
        if requires_valid_bundle and not isValidBundlePath(bundle_path):
            msg = 'Invalid bundle path: %s.' % bundle_path
            logger.error(msg)
            raise ValueError(msg)

        self.release_tag = release_tag
        self.verbose = verbose
        self.force = force
        if bundle_path.endswith('/'):
            self.bundle_path = bundle_path[:-1]
        logger.debug('Init bundle_path: ' + self.bundle_path)
        self.analyzed = False
        self.already_prompted = False
        self.products = []
        self.bundle_url = self.getSvnUrl()


    def listProducts(self, bundle_path=None):
        """return the list of products of a bundle.

        format: [{'path':value, 'url':value, 'revision':value}, ...]
        """
        if bundle_path is None:
            bundle_path = self.bundle_path
        logger.debug('listProducts of bundle: %s' % bundle_path)
        status, output = command('svn pg svn:externals ' + bundle_path)
        products = []
        if status:
            return products
        for line in output:
            if not line or line.startswith('#'):
                continue
            ret = line.split()
            if not ret:
                continue
            path = ret[0]
            url = ret[-1]
            if not (url.startswith('http') or url.startswith('file')):
                if line[0] != '#':
                    logger.warning('Skip invalid svn return line: [%s]' % line)
                continue

            revision = None
            if len(ret) == 3:
                revision = ret[1]
                if revision.startswith('-r'):
                    revision = revision[2:]
                else:
                    logger.warning(
                        'Skipping invalid revision [%s] in line: [%s]' %
                        (revision, line))
                    revision = None
            products.append({'path':path, 'url':url, 'revision':revision})
        return products

    def getSvnUrl(self):
        """Extract the svn url from the bundle path."""
        status, output = command(
            "svn info " + self.bundle_path + " | grep '^URL'",
            do_raise=False)
        if status:
            return None
        if len(output) == 1:
            url_line = output[0].split(':', 1)
            if url_line[0] == 'URL':
                return url_line[1].strip()
        logger.warning('URL not found, invalid output: [%s]' % output)
        return None

    def analyze(self, force=False, show_action=False, verbose=False):
        """Analyze all products.

        This is resource consuming on the SVN repository
        and should be investigated.
        """
        if self.analyzed and not force:
            return
        if not show_action:
            logger.info('Analyze all products ...')
        ret = 0
        products = self.listProducts()
        self.products = []
        for product in products:
            prod = ProductMan(os.path.join(self.bundle_path, product['path']),
                              product['url'], product['revision'],
                              rpath=product['path'])
            prod.analyze()
            if show_action:
                ret = ret | prod.showAction(verbose)
            self.products.append(prod)
        self.analyzed = True
        return ret

    def prompt(self, query):
        """Prompt user for a positive reply."""
        if self.force:
            return
        sys.stdout.write(query)
        res = sys.stdin.readline().strip().lower()
        if res[0] not in 'yo':
            logger.warning('User abort.')
            sys.exit(-2)

    def promptInitialize(self):
        """Prompt user if ready to initialize a product."""
        if self.already_prompted:
            return
        self.prompt('Initialize bundle %s [y/N]: ' % self.bundle_url)
        self.already_prompted = True

    def init(self):
        """Create and commit default files."""
        logger.info('Initialize bundle %s.' % self.bundle_path)
        # check svn tree
        url = self.bundle_url
        path = self.bundle_path
        if not url or os.path.basename(url) != 'trunk':
            logger.error(
                'Expecting a bundle WCPATH that point to a trunk url.')
            return -1
        bundle_url = os.path.dirname(url)
        for folder in ('tags', 'branches'):
            ret, output = command('svn ls %s/%s' % (bundle_url, folder),
                                  do_raise=False)
            if ret:
                logger.error('Missing folder %s/%s.' % (bundle_url, folder))
                return -1
        # check files
        externals_path = os.path.join(path, SVN_EXTERNALS)
        if os.path.exists(externals_path):
            logger.warning('Bundle already initialized')
        else:
            self.promptInitialize()
            status, output = command('svn pg svn:externals %s' % path)
            if status or not output:
                logger.error('No svn:externals defined on %s.' % path)
                return -1
            logger.info('Creating %s file.' % SVN_EXTERNALS)
            f = open(externals_path, 'w+')
            f.write('\n'.join(output))
            f.close()
            command('svn add %s' % externals_path)
            command('svn commit -m"bundleman adding %s" %s' % (
                SVN_EXTERNALS, externals_path))

        return 0

    def showAction(self, verbose=None):
        """List things to do."""
        if verbose is None:
            verbose = self.verbose
        logger.info('List of actions to do:')
        ret = self.analyze(show_action=True, verbose=verbose)
        if not ret:
            logger.info('Ready: All products have been already released.')
        elif ret > 0:
            logger.info('Ready: Going to release some products.')
        else:
            logger.warning('Bundle not ready to be released.')
        return ret

    def doAction(self):
        """Do action for all products."""
        self.analyze()
        ret = 0
        for product in self.products:
            ret = ret | product.doAction()
        if ret or not self.release_tag:
            logger.error('Bundle is not ready to be released.')
            return ret
        ret = self.tag()
        return ret


    def tag(self):
        """Create a bundle tags/release_tag."""
        release_tag = self.release_tag
        logger.info('Create a bundle tag %s' % release_tag)

        # check bundle url
        bundle_url = self.bundle_url

        tag_url = computeTagUrl(bundle_url, release_tag)
        if tag_url is None:
            logger.error('Invalid bundle url: %s' % bundle_url)
            return -1
        ret, output = command('svn ls %s' % tag_url, do_raise=False)
        if not ret:
            logger.error('Bundle tag %s already exists.' % tag_url)
            return -1

        # analyze products
        self.analyze(force=True)
        bad_products = []
        products = []
        for product in self.products:
            if product.status != 'use_tag':
                bad_products.append(product)
            products.append({'path': product.rpath,
                             'revision': product.revision,
                             'url': product.tag_url})
        if bad_products:
            logger.warning('Sorry found product(s) not ready:')
            for product in bad_products:
                print str(product)
            return -1

        # create bundle
        logger.info('Creating bundle %s' % tag_url)
        createBundle(tag_url, products, release_tag, bundle_url)
        return 0


    def branch(self):
        """Create a branch for all products from a bundle tag."""
        release_tag = self.release_tag
        hash_tag = getHashTag(release_tag)
        bundle_tag_url = computeTagUrl(self.bundle_url, release_tag)
        if not bundle_tag_url:
            logger.error('Invalid source url: %s' % self.bundle_url)
            return -1
        bundle_branch_url = bundle_tag_url.replace('/tags/', '/branches/')
        logger.info('Branching %s -> %s hash_tag: %s.' %
                    (bundle_tag_url, bundle_branch_url, hash_tag))
        ret, output = command('svn ls %s' % bundle_tag_url, do_raise=False)
        if ret:
            logger.error('Tag not found. You need to release %s first.' %
                         release_tag)
            return -1
        ret, output = command('svn ls %s' % bundle_branch_url, do_raise=False)
        if not ret:
            logger.error('Branch %s already exists.' % bundle_branch_url)
            return -1
        products = self.listProducts(bundle_tag_url)
        branch_products = []

        # create a branch for each product
        for product in products:
            product_url = product['url']
            parent = os.path.dirname(product_url)
            ret = -1
            if os.path.basename(parent) == 'tags':
                ret, output = command('svn ls %s/CHANGES' % product_url,
                                      do_raise=False)
            if ret:
                # not a versionned product keep it asis
                branch_products.append(product)
                continue

            branch_url = os.path.dirname(parent) + '/branches/' + hash_tag
            ret, output = command('svn ls %s' % branch_url, do_raise=False)
            if not ret:
                logger.warning('Branch %s already exists.' % branch_url)
            else:
                command('svn copy -m"bundleman branch product %s release %s"'
                        '-r%s %s %s' %
                        (product['path'], hash_tag, product['revision'],
                         product_url, branch_url))
            branch_products.append({'path': product['path'],
                                    'url': branch_url})

        # create a bundle branch
        logger.info('Creating bundle %s' % bundle_branch_url)
        createBundle(bundle_branch_url, branch_products, release_tag)
        return bundle_branch_url


    def prepareBundleArchive(self, bundle_path, bundle_name):
        """Prepare a bundle checkout before creating an archive."""
        for product in self.products:
            product_path = os.path.join(bundle_path, product.rpath)
            version = '%s-%s\n' % (product.version[1], product.version[2])
            prepareProductArchive(product_path, product.bm_versioned, version)
        # add version
        f = open(os.path.join(bundle_path, 'version.txt'), 'w+')
        f.write('%s\n' % bundle_name)
        f.close()


    def buildArchive(self, archive_dir, remote_path=None,
                     archive_root=None, archive_name=None, analyze=True):
        """Create a tar gz archive in archive_dir."""
        if analyze:
            self.analyze(force=True)
        products = self.products
        products_ready = True
        for product in products:
            if product.status != 'use_tag':
                logger.error('Product %s not ready to be archived.' %
                             product.path)
                product.showAction()
                products_ready = False
        if not products_ready:
            return -1

        if archive_name is None:
            archive_name = '%s.tgz' % self.release_tag
        archive_path = os.path.join(archive_dir, archive_name)
        logger.info('Creating archive: %s' % archive_path)

        if not archive_root:
            # archive root is the root folder inside the archive
            archive_root = self.release_tag

        # extract tag
        tmpdir = mkdtemp()
        bundle_name = self.release_tag
        bundle_path = os.path.join(tmpdir, archive_root)
        bundle_tag_url = computeTagUrl(self.bundle_url, bundle_name)
        command('svn -q export %s %s' % (bundle_tag_url, bundle_path))

        if not os.path.exists(bundle_path):
            # svn export don't complain on invalid url
            logger.error('Tag %s not found, use --release first.' %
                         bundle_tag_url)
            return -1

        # prepare bundle and products
        self.prepareBundleArchive(bundle_path, bundle_name)

        # add MD5SUMS
        command('cd %s; find . -type f -not -name MD5SUMS -print0 '
                '| xargs -0 md5sum > MD5SUMS' % bundle_path)

        # tarball
        command('cd %s; tar czf %s %s' % (tmpdir, archive_path, archive_root))
        command('rm -rf %s' % tmpdir)
        command('chmod 644 %s' % archive_path)
        logger.info('Archive: %s ready.' % archive_path)
        if remote_path:
            logger.info("scp archive to %s" % remote_path)
            command("scp %s %s" % (archive_path, remote_path))
        return 0


    def addChangelog(self, tag1, tag2):
        """Add a global CHANGELOG.txt file to the tag2 url."""
        logger.info('Adding a global CHANGELOG.txt')
        try:
            changelog = self.getChangelog(tag1, tag2)
        except ValueError:
            return -1
        f = NamedTemporaryFile('w+', prefix='bm-')
        f.write(changelog)
        f.flush()
        tag_url = computeBundleTagUrl(self.bundle_url, tag2)
        command('svn import %s %s/CHANGELOG.txt '
                '-m"bundelman add CHANGELOG.txt to %s"' %
                (f.name, tag_url, tag_url))
        f.close()
        return 0

    def changelog(self, tag1, tag2):
        """Output the changelog between 2 bundle tags."""
        try:
            print self.getChangelog(tag1, tag2)
        except ValueError:
            return -1
        return 0


    def getChangelog(self, tag1, tag2):
        """Return a changelog between 2 bundle tags."""
        # compute tags url
        url = self.bundle_url
        tag1_url = computeBundleTagUrl(url, tag1)
        tag2_url = computeBundleTagUrl(url, tag2)
        if not tag1_url or not tag2_url:
            msg = 'Invalid bundle url: %s' % url
            logger.error(msg)
            raise ValueError(msg)
        return self._changelog(tag1, tag2, tag1_url, tag2_url)


    def changelog_url(self, tag1_url, tag2_url):
        """Output a changelog between to bundle urls."""
        tag1 = os.path.basename(tag1_url)
        tag2 = os.path.basename(tag2_url)
        try:
            print self._changelog(tag1, tag2, tag1_url, tag2_url)
        except ValueError:
            return -1
        return 0


    def _changelog(self, tag1, tag2, tag1_url, tag2_url):
        """Output a changelog between to bundle url."""
        # check that tags exists
        for tag_url in (tag1_url, tag2_url):
            ret, output = command('svn ls %s' % tag_url, do_raise=False)
            if ret:
                msg = 'Tags %s not found.' % tag_url
                logger.error(msg)
                raise ValueError(msg)

        # get list of products
        prod1_infos = self.listProducts(tag1_url)
        prod2_infos = self.listProducts(tag2_url)
        prod1_list = [prod.get('path') for prod in prod1_infos]
        prod2_list = [prod.get('path') for prod in prod2_infos]

        new_products = [prod for prod in prod2_list if prod not in prod1_list]
        removed_products = [prod for prod in prod1_list
                            if prod not in prod2_list]
        check_products = [prod for prod in prod2_list if prod in prod1_list]
        changed_products = []

        requires = []
        features = []
        bug_fixes = []
        int_features = []
        for prod in check_products:
            prod1 = [x for x in prod1_infos if x.get('path') == prod][0]
            prod2 = [x for x in prod2_infos if x.get('path') == prod][0]
            if prod1['url'] == prod2['url']:
                continue
            changed_products.append((prod, os.path.basename(prod1['url']),
                                     os.path.basename(prod2['url'])))
            # we ask for changes between HISTORY files
            hist1 = os.path.join(prod1['url'], 'HISTORY')
            hist2 = os.path.join(prod2['url'], 'HISTORY')

            ret, output = command('svn diff %s %s' % (hist1, hist2),
                                  do_raise=False)
            if ret:
                logger.warning('svn diff failed on product %s' % prod )
                continue
            diff = [line[1:] for line in output
                    if line.startswith('+') and not line.startswith('++')]
            ret = parseNuxeoHistory('\n'.join(diff))
            requires.extend(['[%s] %s'% (prod, line) for line in ret[0]])
            features.extend(['[%s] %s'% (prod, line) for line in ret[1]])
            bug_fixes.extend(['[%s] %s'% (prod, line) for line in ret[2]])
            int_features.extend(['[%s] %s'% (prod, line) for line in ret[3]])

        output_buffer = []
        output = output_buffer.append
        output(rst_title("CHANGELOG between bundles %s and %s" %
                         (tag1, tag2), 0))
        output("New tag: %s" % tag2_url)
        output("Old tag: %s" % tag1_url)
        if new_products:
            output(rst_title('New products', 2))
            output('\n'.join(new_products))
        if removed_products:
            output(rst_title('Removed products', 2))
            output('\n'.join(removed_products))
        if changed_products:
            output(rst_title('Changed products', 2))
            for prod in changed_products:
                output('* %s \t %s -> %s' % (prod[0], prod[1], prod[2]))
        if requires:
            output(rst_title('Requires', 3))
            output('* ' + '\n* '.join(requires))
        if features:
            output(rst_title('Features', 3))
            output('* ' + '\n* '.join(features))
        if bug_fixes:
            output(rst_title('Bug fixes', 3))
            output('* ' + '\n* '.join(bug_fixes))
        if int_features:
            output(rst_title('Internal features', 3))
            output('* ' + '\n* '.join(int_features))
        output('\n')
        return '\n'.join(output_buffer)


class BundleManProgram:
    """Program class"""
    DEFAULT_LOG_PATH = '~/bundleman.log'
    USAGE = """%prog [options] [WCPATH]

%prog is a bundle release manager. See BundleMan documentation for more
information.

WCPATH is a svn working copy path of a bundle, using current path if not
specified.

A bundle is an suite of products, this suites is defined using svn:externals
property of the bundle folder.

A bundle follows the classic trunk/tags/branches svn tree.

Products may be versionned using bm-product tool.

Examples
========
  %prog
                        Display status and action to be done.

  %prog --init
                        Initialize WCPATH bundle:
                          - add svn-externals file to trunk

  %prog --release APPrc1
                        Create release bundle in tags/APPrc1 that point to
                        released products.

  %prog --release APPrc1 -a
                        Create a release and a targz archive in one step.

  %prog --archive APPrc1 -o /tmp
                        Create a targz archive in /tmp directory.
                        The tarball contains a MD5SUMS file and can be
                        verified using `md5sum -c MD5SUMS`.

  %prog --archive APPrc1 --archive-root-directory Products
                        Create a targz archive of APPrc1 release with a root
                        folder named Products.

  %prog --archive APPrc1 --archive-root-directory Products --archive-name APP-full.tar.gz
                        Create a targz archive of APPrc1 release with a root
                        folder named Products and an archive named APP-full.tar.gz.

  %prog --branch APPrc1
                        Create a branch bundle in branch/APPrc1 that point to
                        branched products.
                        A product branch will be created for each versioned
                        products. The branch name use a hash(APPrc1) key.

  %prog --changelog APPrc1:APPrc2
                        Output a global bundle changelog between bundle tags.

  %prog --release APPrc2 --changelog APPrc1: -a -o /tmp --scp bar:/tmp
                        Create a release with a global changelog, build
                        the targz archive, scp it to bar:/tmp in one step.
"""
    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        cur_path = os.path.abspath(os.path.curdir)
        self.bundle_path = cur_path
        self.release_tag = None
        options = self.parseArgs(argv)
        self.options = options
        if options.debug:
            level = logging.DEBUG
        else:
            level = logging.INFO
        initLogger(options.log_file, True, level)
        logger.debug('### RUN BundleMan from %s args: %s ' %
                     (cur_path, ' '.join(argv)))

    def parseArgs(self, argv):
        """Parse programs args."""
        parser = OptionParser(self.USAGE, formatter=TitledHelpFormatter(),
                              version="BundleMan %s" % __version__)

        def releasecb(option, opt, value, parser):
            """Parser callback."""
            setattr(parser.values, option.dest, value)
            setattr(parser.values, 'release', True)

        def branchcb(option, opt, value, parser):
            """Parser callback."""
            setattr(parser.values, option.dest, value)
            setattr(parser.values, 'branch', True)

        def archivecb(option, opt, value, parser):
            """Parser callback."""
            setattr(parser.values, option.dest, value)
            setattr(parser.values, 'archive', True)

        parser.add_option("-s", "--status", action="store_true",
                          help="Show action to be done.",
                          default=True)
        parser.add_option("-i", "--init", action="store_true",
                          help="Initialize the bundle working copy.",
                          default=False)
        parser.add_option("--release", type="string", action="callback",
                          dest="release_tag", callback=releasecb,
                          help="Release the bundle.", default=None)
        parser.add_option("-a",  action="store_true",
                          dest="archive",
                          help="Build a tar gz archive, must be used with "
                          "--release option.", default=False)
        parser.add_option("--archive",  type="string", action="callback",
                          dest="release_tag", callback=archivecb,
                          help="Build a tar gz archive from an existing "
                          "RELEASE_TAG.", default=None)
        parser.add_option("--archive-root-directory", type="string",
                          dest="archive_root",
                          help="The name of the root directory in the archive,"
                          " default is RELEASE_TAG.")
        cur_path = os.path.abspath(os.path.curdir)
        parser.add_option("-o", "--output-directory", type="string",
                          dest="output_dir",
                          help="Directory to store the archive.",
                          default=cur_path)
        parser.add_option("-A", "--archive-name", type="string",
                          dest="archive_name",
                          help="Name of the archive.")
        parser.add_option("--scp", type="string", dest="remote_path",
                          help="scp the archive to a REMOTE_PATH.")
        parser.add_option("--branch", type="string", action="callback",
                          dest="release_tag", callback=branchcb,
                          help="Branch the bundle release.", default=None)
        parser.add_option("--changelog", type="string", default=None,
                          dest="TAG1:TAG2",
                          help="Output a changelog between 2 bundle tags. "
                          "If TAG2 is missing it uses the RELEASE_TAG.")
        parser.add_option("--changelog-url", type="string", default=None,
                          dest="TAG1_URL:TAG2_URL",
                          help="Output a changelog between 2 bundle url tags.")
        parser.add_option("-f", "--force", action="store_true",
                          help="No prompt during --init.", default=False)
        parser.add_option("-l", "--log-file", type="string",
                          dest="log_file",
                          help="The log file path. Default is %s." %
                          self.DEFAULT_LOG_PATH,
                          default=os.path.expanduser(self.DEFAULT_LOG_PATH))
        parser.add_option("-v", "--verbose", action="store_true",
                          help="Verbose output", default=False)
        parser.add_option("-d", "--debug", action="store_true",
                          help="Debug output", default=False)

        parser.set_defaults(release=False, branch=False, archive=False)
        options, args = parser.parse_args(argv)
        if len(args) == 1:
            self.bundle_path = os.path.abspath(args[0])
        if options.archive and not options.release_tag:
            parser.error("-a option must be used with --release option.")
        changelog = getattr(options, 'TAG1:TAG2')
        if changelog:
            if not changelog.count(':'):
                parser.error("Invalid value for '--changelog' option, "
                             "expects a TAG_RELEASE1:TAG_RELEASE2 input.")
        options.changelog = changelog
        changelog_url = getattr(options, 'TAG1_URL:TAG2_URL')
        if changelog_url:
            if changelog_url.count(':') != 3:
                parser.error("Invalid value for '--changelog-url' option, "
                             "expects a TAG1_URL:TAG2_URL input.")
        options.changelog_url = changelog_url

        return options


    def run(self):
        """Main."""
        options = self.options
        try:
            requires_valid_bundle = True
            if options.changelog_url:
                requires_valid_bundle = False
            bman = BundleMan(self.bundle_path, options.release_tag,
                             verbose=options.verbose,
                             force=options.force,
                             requires_valid_bundle=requires_valid_bundle)
        except ValueError:
            return -1
        if options.changelog_url:
            ret = options.changelog_url.split(':')
            tag1_url = ':'.join(ret[:2])
            tag2_url = ':'.join(ret[2:])
            ret = bman.changelog_url(tag1_url.strip(), tag2_url.strip())
        elif options.init:
            ret = bman.init()
        elif options.release:
            ret = bman.doAction()
            if not ret and options.changelog:
                tag1 = options.changelog.split(':')[0]
                tag2 = options.release_tag
                ret = bman.addChangelog(tag1, tag2)
            if not ret and options.archive:
                # Optimization: we donnot need to analyze the products again
                # (which is a resource consuming action on the SVN repository)
                # to build the archive after the release process which has
                # already analyze the products twice in the process.
                ret = bman.buildArchive(options.output_dir,
                                        options.remote_path,
                                        options.archive_root,
                                        options.archive_name,
                                        analyze=False,
                                        )
        elif options.changelog:
            tag1, tag2 = options.changelog.split(':')
            ret = bman.changelog(tag1.strip(), tag2.strip())
        elif options.archive:
            ret = bman.buildArchive(options.output_dir,
                                    options.remote_path,
                                    options.archive_root,
                                    options.archive_name,
                                    )
        elif options.release_tag:
            ret = bman.branch()
        else:
            ret = bman.showAction()

        return ret

def main():
    prog = BundleManProgram()
    ret = prog.run()
    sys.exit(ret)

if __name__ == '__main__':
    main()
