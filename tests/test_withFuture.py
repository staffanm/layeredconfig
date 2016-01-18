#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from builtins import *
from future import standard_library
standard_library.install_aliases()

import os
import sys

if sys.version_info < (2, 7, 0):  # pragma: no cover
    import unittest2 as unittest
else: 
    import unittest

from layeredconfig import LayeredConfig, Defaults, Environment


class TestFuture(unittest.TestCase):

    def test_newint(self):
        os.environ['FERENDA_DOWNLOADMAX'] = '3'
        config = LayeredConfig(Defaults({'downloadmax': int}),
                               Environment(prefix="FERENDA_"))
        self.assertEqual(3, config.downloadmax)
        self.assertIsInstance(config.downloadmax, int)
