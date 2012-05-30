# BundleMan Makefile
# $Id: Makefile 53582 2009-03-26 19:52:05Z bdelbosc $
#
.PHONY: build clean

TARGET := bertha_:~/public_public_html/bundleman


build:
	python setup.py build

test:
	python setup.py test

pkg: sdist

sdist:
	python setup.py sdist

distrib:
	-scp dist/bundleman-*.tar.gz $(TARGET)/snapshots

cheesecake: sdist
	ls dist/bundleman*.tar.gz | xargs cheesecake_index -v --path

install:
	python setup.py install

register:
	-python setup.py register

uninstall:
	-rm -rf /usr/lib/python2.3/site-packages/bundleman*
	-rm -rf /usr/lib/python2.4/site-packages/bundleman*
	-rm -rf /usr/lib/python2.5/site-packages/bundleman*
	-rm -f /usr/local/bin/bm-bundle /usr/local/bin/bm-product
	-rm -f /usr/bin/bm-bundle /usr/bin/bm-product

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST
