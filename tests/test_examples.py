#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
test_layeredconfig
----------------------------------

Tests for `layeredconfig` module.
"""

import os
import sys
if sys.version_info < (2, 7, 0):  # pragma: no cover
    import unittest2 as unittest
else: 
    import unittest
import shutil
import six


class Examples(unittest.TestCase):

    def _test_pyfile(self, pyfile, want=True, comparator=None, expectexit=False):
        # temporarily redefine the print function in current context
        l = locals()
        l['print'] = lambda x: None
        with open(pyfile) as fp:
            pycode = compile(fp.read(), pyfile, 'exec')
        try:
            result = six.exec_(pycode, globals(), l)
            # the exec:ed code is expected to set return_value
            got = locals()['return_value']
            if not comparator:
                comparator = self.assertEqual
            comparator(want, got)
        except SystemExit as e:
            if not expectexit:
                raise e

    def test_firststep(self):
        self._test_pyfile("docs/examples/firststep.py")
        os.unlink("myapp.ini")

    def test_usage(self):
        shutil.copy2("docs/examples/myapp.ini", os.getcwd())
        self._test_pyfile("docs/examples/usage.py")
        os.unlink("myapp.ini")

    def test_argparse(self):
        _stdout = sys.stdout
        try:
            devnull = open(os.devnull, "w")
            sys.stdout = devnull
            self._test_pyfile("docs/examples/argparse-example.py", expectexit=True)
        finally:
            sys.stdout = _stdout
            devnull.close()
        os.unlink("myapp.ini")

