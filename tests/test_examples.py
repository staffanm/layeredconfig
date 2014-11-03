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

    def _test_pyfile(self, pyfile, want=True, comparator=None):
        # temporarily redefine the print function in current context
        l = locals()
        l['print'] = lambda x: None
        with open(pyfile) as fp:
            pycode = compile(fp.read(), pyfile, 'exec')
        result = six.exec_(pycode, globals(), l)
        # the exec:ed code is expected to set return_value
        got = locals()['return_value']
        if not comparator:
            comparator = self.assertEqual
        comparator(want, got)

    def test_firststep(self):
        self._test_pyfile("docs/examples/firststep.py")
        os.unlink("myapp.ini")

    def test_usage(self):
        shutil.copy2("docs/examples/myapp.ini", os.getcwd())
        self._test_pyfile("docs/examples/usage.py")
        os.unlink("myapp.ini")
