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
"""utils for bundleman

$Id: $
"""
import os
import re
import logging
from tempfile import mkdtemp
from commands import getstatusoutput

# the name of the file that contains the svn:externals property of a bundle
SVN_EXTERNALS = 'svn-externals'
logger = logging.getLogger('bm.utils')
g_logger_exists = False

def initLogger(log_path, console=True, level=logging.INFO):
    """Initialize the logger."""
    global g_logger_exists
    if g_logger_exists:
        return
    bmlogger = logging.getLogger('bm')
    if console:
        hdlr = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        hdlr.setFormatter(formatter)
        hdlr.setLevel(level)
        bmlogger.addHandler(hdlr)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s')
    hdlr = logging.FileHandler(log_path)
    hdlr.setFormatter(formatter)
    bmlogger = logging.getLogger('bm')
    bmlogger.addHandler(hdlr)
    bmlogger.setLevel(logging.DEBUG)
    g_logger_exists = True

def command(cmd, do_raise=True):
    """Return the status, output as a line list."""
    extra = 'LC_ALL=C '
    logger.debug('Run: ' + extra + cmd)
    status, output = getstatusoutput(extra +cmd)
    if status:
        if do_raise:
            logger.error('[%s] return status: [%d], output: [%s]' %
                         (extra + cmd, status, output))
            raise RuntimeError('Invalid return code: %s' % status)
        else:
            logger.debug('return status: [%d]' % status)
    if output:
        output = output.split('\n')
    return (status, output)


def isSvnCompatible(minimum='1.2'):
    """Check if svn version is >= minimum."""
    ret, output = command('svn --version')
    match = re.search('[\d\.]+', output[0])
    if match is None:
        logger.error('svn --version return an unknow output')
        return False
    version = match.group().split('.')
    version.reverse()
    version_min = minimum.split('.')
    version_min.reverse()
    while version_min and version:
        if int(version_min.pop()) > int(version.pop()):
            logger.warning('Minimum svn version is %s, current is %s' % (
                minimum, match.group()))
            return False
    return True

def parseNuxeoVersionFile(content):
    """Parse a nuxeo product VERSION content.

    Return a tuple (name, version, release) or raise a ValueError."""
    lines = [line.strip() for line in content.split('\n')
             if line.strip() and not line.startswith('#')]
    name = version = release = None
    for line in lines:
        if line.find('=') > 0:
            key, value = line.split('=')
            if key == 'PKG_NAME':
                name = value.strip()
            elif key == 'PKG_VERSION':
                version = value.strip()
            elif key == 'PKG_RELEASE':
                release = value.strip()
    if not (name and version and release):
        raise ValueError, 'invalid VERSION content:\n%s.' % content
    return [name, version, release]

def parseVersionString(version):
    """Return a tuple (majeur, mineur, bugfix, branch) from a version string.

    >>> from utils import parseVersionString
    >>> parseVersionString('1.3')
    [1, 3, 0, '']
    >>> parseVersionString('1.3.2')
    [1, 3, 2, '']
    >>> parseVersionString('1.3.2-user-refactor')
    [1, 3, 2, 'user-refactor']

    note that majeur, mineur, bugfix are integer."""
    majeur = mineur = bugfix = 0
    branch = ''
    if not version:
        return [majeur, mineur, bugfix, branch]
    tmp = version.split('-', 1)
    if len(tmp) > 1:
        branch = tmp[1]
    tmp = tmp[0].split('.')
    len_tmp = len(tmp)
    majeur = int(tmp[0])
    if len_tmp > 1:
        mineur = int(tmp[1])
    if len_tmp > 2:
        bugfix = int(tmp[2])
    return [majeur, mineur, bugfix, branch]


def parseNuxeoChanges(content):
    """Parse CHANGES and return a list

    return (requires, features, bugfix, internal features)."""
    requires = []
    features = []
    bug_fixes = []
    int_features = []
    section = requires
    for line in content.split('\n'):
        if line.startswith('- ') or line.startswith('  '):
            if len(line) > 2:
                section.append(line)
        else:
            line = line.lower()
            if line.startswith('requires'):
                section = requires
            elif line.startswith('new feature'):
                section = features
            elif line.startswith('bug fixes'):
                section = bug_fixes
            elif line.startswith('new internal features'):
                section = int_features
    return (requires, features, bug_fixes, int_features)

def parseNuxeoHistory(content):
    """Parse an HISTORY file content or a part of it.

    return (requires, features, bugfix, internal features)."""
    changes = re.split('=======*', content)
    changes = filter(None, [change.strip() for change in changes])
    changes = [change for change in changes
               if change.lower().count('\nrequires')]
    requires = []
    features = []
    bug_fixes = []
    int_features = []
    for change in changes:
        ret = parseNuxeoChanges(change)
        requires.extend(ret[0])
        features.extend(ret[1])
        bug_fixes.extend(ret[2])
        int_features.extend(ret[3])

    return (requires, features, bug_fixes, int_features)


def parseZopeVersionFile(content):
    """Parse a zope product version.txt content.

    Return a tuple (name, version, release) or raise a ValueError

    Format can be:
    Foo-1.2-3
    Foo 1.2.3-1
    1.2-1
    2
    """
    name = []
    release = version = None
    info = re.split('[\ \-]', content.strip())
    for text in info:
        if re.search('[a-zA-Z\_]', text):
            name.append(text)
        if re.match('^[\d\.]+$', text):
            if not version:
                version = text
            elif not release:
                release = text
            else:
                raise ValueError, "Too many numbers: '%s'." % content
    if len(name):
        name = '-'.join(name)
    else:
        name = None
    if name == 'CMF':
        # all CMF products have version CMF-1.5.0
        # we use the folder name as name
        name = None
    if not name and not version and not release:
        raise ValueError, "Invalid pkg name: '%s'." % content
    if not release:
        release = '1'
    return [name, version, release]


def computeTagUrl(url, tag_name):
    """Return a svn tag url from a working svn url.

    >>> from utils import computeTagUrl
    >>> computeTagUrl('products/bar/trunk', '1.0.0')
    'products/bar/tags/1.0.0'
    >>> computeTagUrl('products/bar/trunk/', '1.0.0')
    'products/bar/tags/1.0.0'
    >>> computeTagUrl('products/bar/branches/user-refactor', '1.0.0')
    'products/bar/tags/1.0.0'
    >>> computeTagUrl('products/bar/branches/user-refactor', \
                      '1.0.0-user-refactor')
    'products/bar/tags/1.0.0-user-refactor'
    >>> computeTagUrl('products/foo/tags/1.0.0', '1.0.0') is None
    True
    >>> computeTagUrl('products/bar/tags/1.2.0', '1.0.0') is None
    True
    >>> computeTagUrl('/vendor/foo/branches/user-bar', '2.2') is None
    True
    >>> computeTagUrl('/3dparty/foo/bar/trunk', '2.2') is None
    True
    """
    if url.endswith('/'):
        url = url[:-1]
    tag = '/tags/' + tag_name
    tag_url = None
    if not url or '/tags/' in url or '/vendor/' in url or '/3dparty/' in url:
        return None
    if url.endswith('trunk'):
        tag_url = os.path.dirname(url) + tag
    else:
        parent = os.path.dirname(url)
        if os.path.basename(parent) == 'branches':
            tag_url = os.path.dirname(parent) + tag
    return tag_url


def computeBundleTagUrl(url, tag_name):
    """Return a svn tag url from a working bundle svn url.

    >>> from utils import computeBundleTagUrl
    >>> computeBundleTagUrl('bundles/app/trunk', 'APP')
    'bundles/app/tags/APP'
    >>> computeBundleTagUrl('bundles/app/branches/APPrc1', 'APP')
    'bundles/app/tags/APP'
    >>> computeBundleTagUrl('bundles/app/tags/APPrc1', 'APPrc2')
    'bundles/app/tags/APPrc2'
    >>> computeBundleTagUrl('bundles/vendor/app', 'APPrc1') is None
    True
    """
    tag_url = None
    if url.endswith('/trunk'):
        tag_url = url.replace('/trunk', '/tags/' + tag_name)
    elif url.count('/branches/') or url.count('/tags'):
        tmp = url.find('/branches/')
        if tmp == -1:
            tmp = url.find('/tags/')
        tag_url = url[:tmp] + '/tags/' + tag_name
    return tag_url


def createBundle(url, products, tag, from_bundle=None):
    """Create a bundle at url with products.

    Expecting a products list: [{'path':..., 'revision':.., 'url':...} ...
    """
    # create bundle
    if from_bundle is not None:
        command('svn -m"bundleman create bundle %s from %s" cp %s %s' %
                (tag, from_bundle, from_bundle, url))
    else:
        command('svn -m"bundleman create bundle %s" mkdir %s' %
                (tag, url))
    lines = []
    for product in products:
        if product.get('revision'):
            lines.append('%s -r%s %s' % (product['path'],
                                         product['revision'],
                                         product['url']))
        else:
            lines.append('%s   %s' % (product['path'], product['url']))
    tmpdir = mkdtemp()
    command('svn co %s %s' % (url, tmpdir))
    svn_externals = os.path.join(tmpdir, SVN_EXTERNALS)
    f = open('%s' % svn_externals, 'w+')
    content = '\n'.join(lines) + '\n'
    f.write(content)
    f.close()
    command('svn add %s' % svn_externals)
    command('svn ps svn:externals -F %s %s' % (svn_externals,
                                               tmpdir))
    command('svn -m "bundleman setting %s for %s" commit %s' %
            (SVN_EXTERNALS, tag, tmpdir))
    command('rm -rf %s' % tmpdir)
    return 0

def getHashTag(tag):
    """Return a hash tag."""
    return 'rel' + str(abs(hash(tag)))

def rst_title(title, level=1):
    """Return a rst title."""
    rst_level = ['=', '=', '-', '~']
    if level == 0:
        rst = [rst_level[level] * len(title)]
    else:
        rst = ['']
    rst.append(title)
    rst.append(rst_level[level] * len(title))
    rst.append('')
    return '\n'.join(rst)


def prepareProductArchive(path, bm_versioned, version):
    """Renaming HISTORY, removing CHANGES creating version.txt."""
    if bm_versioned:
        try:
            os.rename(os.path.join(path, 'HISTORY'),
                      os.path.join(path, 'CHANGELOG.txt'))
            os.remove(os.path.join(path, 'CHANGES'))
        except OSError:
            logger.warning('Got an exception while renaming HISTORY '
                           'and CHANGES')
    version_path = os.path.join(path, 'version.txt')
    if not os.path.exists(version_path):
        f = open(version_path, 'w+')
        f.write(version + '\n')
        f.close()

