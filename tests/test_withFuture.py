#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
try:
    from builtins import *
    from future import standard_library
    standard_library.install_aliases()
except:
    # we might be on py3.2, which the future library doesn't support
    pass 

import os
import sys

if sys.version_info < (2, 7, 0):  # pragma: no cover
    import unittest2 as unittest
else: 
    import unittest

from layeredconfig import LayeredConfig, Defaults, Environment, INIFile

@unittest.skipIf (sys.version_info[0] == 3 and sys.version_info[1] < 3,
                  "Python 3.2 and lower doesn't support the future module")
class TestFuture(unittest.TestCase):

    def test_newint(self):
        os.environ['FERENDA_DOWNLOADMAX'] = '3'
        config = LayeredConfig(Defaults({'downloadmax': int}),
                               Environment(prefix="FERENDA_"))
        self.assertEqual(3, config.downloadmax)
        self.assertIsInstance(config.downloadmax, int)
