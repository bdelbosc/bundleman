"""Implement a python setup.py test command.

Taken from Darren's Notebook http://sevenroot.org/dlc/2002/11/using-distutils/

$Id: $
"""
import os
from os.path import splitext, basename, join as pjoin
from glob import glob
from distutils.core import Command
from unittest import TextTestRunner, TestLoader

class TestCommand(Command):
    """Add a test command."""
    user_options = [ ]

    def initialize_options(self):
        """init."""
        self._dir = os.getcwd()

    def finalize_options(self):
        """finalize."""
        pass

    def run(self):
        """Finds all the tests modules in tests/, and runs them."""
        testfiles = [ ]
        for test in glob(pjoin(self._dir, 'tests', 'test_*.py')):
            if not test.endswith('__init__.py'):
                testfiles.append('.'.join(
                    ['tests', splitext(basename(test))[0], 'test_suite'])
                )
        testfiles.sort()
        testfiles.reverse()
        tests = TestLoader().loadTestsFromNames(testfiles)
        runner = TextTestRunner(verbosity = 1)
        runner.run(tests)
