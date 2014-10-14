# -*- coding: utf-8 -*-

import os
import sys

class ConfigSource(object):
    pass


class Defaults(ConfigSource):
    """This source is initialized with a dict."""
    def __init__(self, defaults={}, writable=False):
        self.conf = defaults

    
class INIFile(ConfigSource):
    def __init__(self, inifilename=None):
        self.config = None


class Environment(ConfigSource):
    def __init__(self, environ=os.environ, prefix="", lowerize=True):
        self.config = None


class Commandline(ConfigSource):
    def __init__(self, argv=sys.argv):
        self.config = None


class LayeredConfig(object):

    def __init__(self, cascade=False, writable=True, *sources):
        """Creates a config object from zero or more sources.

        If no sources are given, the config object is blank, but you
        can still set values and read them back later.
        """
        self.sources = sources
