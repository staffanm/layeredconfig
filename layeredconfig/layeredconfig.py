# -*- coding: utf-8 -*-

import os
import sys


try:
    from collections import OrderedDict
except ImportError: # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict

class ConfigSource(object):

    
    def register_conversion(type, func):
        """
        >>> def convert_complex(s):
        ...     return complex(s)
        >>> ConfigSource.register_conversion(complex, convert_complex)
        >>> # now type conversion can handle complex numbers
        """
        pass
        
    def _type_value(self, key, value):
        """Find appropriate method/class constructor to convert a
           string value to the correct type IF we know the correct
           type."""

        def boolconvert(value):
            # not all bools should be converted, see test_typed_commandline
            if value == "True":
                return True
            elif value == "False":
                return False
            else:
                return value
            
        def listconvert(value):
            # this function is called with both string represenations
            # of entire lists and simple (unquoted) strings. The
            # ast.literal_eval handles the first case, and if the
            # value can't be parsed as a python expression, it is
            # returned verbatim (not wrapped in a list, for reasons)
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError):
                return value

        def datetimeconvert(value):
            try:
                return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        # find the appropriate defaults object. In the case of
        # cascading, could be any parent that has a key key.
        defaults = self._defaults  # base case
        if self._cascade:
            cfg_obj = self
            while cfg_obj is not None:
                if key in cfg_obj._defaults:
                    defaults = cfg_obj._defaults
                    break  # done!
                if hasattr(cfg_obj, '_parent'):
                    cfg_obj = cfg_obj._parent
                else:
                    cfg_obj = None

        if key in defaults:
            if type(defaults[key]) == type:
                # print("Using class for %s" % key)
                t = defaults[key]
            else:
                # print("Using instance for %s" % key)
                t = type(defaults[key])
        else:
            t = str

        if t == bool:
            t = boolconvert
        elif t == list:
            t = listconvert
        elif t == datetime.datetime:
            t = datetimeconvert
        # print("Converting %r to %r" % (value,t(value)))
        return t(value)


class Defaults(ConfigSource):
    def __init__(self, defaults={}, writable=False, identifier="defaults"):
        """
        This source is initialized with a dict.

        :param defaults: A dict with configuration keys and values. If
                             any values are dicts, these are turned into
                             nested config objects.
        :type defaults: dict
        """
        self.source = defaults

    def subsections(self):
        for (k, v) in self.source.items():
            if isinstance(v, dict):
                yield k

    def subsection(self, key):
        return Defaults(self.source[key])

    def has(self, k):
        return k in self.source

    def get(self, k):
       return self.source[k]

    def set(self, k, v):
        self.source[k] = v
       
    def __iter__(self):
        return self.source.__iter__()  # or "for k in self.source: yield k"
        # what about subsections?
        

class INIFile(ConfigSource):
    def __init__(self, inifilename=None, identifier="inifile"):
        """
        :param inifile: The name of a ini-style configuration file. The
                        file should have a top-level section named
                        __root__, whose keys are turned into top-level
                        configuration parameters. Any other sections in
                        this file are turned into nested config
                        objects.
        :type inifile: str
        """
        self.config = None
        if not inifilename:
            self._configparser = None
            return
        if not os.path.exists(inifilename):
            logging.warn("INI file %s does not exist" % inifilename)
            self._configparser = None
            return

        self._configparser = configparser.ConfigParser(dict_type=OrderedDict)
        self._configparser.read(inifilename)

        if self._configparser.has_section('__root__'):
            self._load_inifile_section('__root__')
        for sectionkey in self._configparser.sections():

            # Do we have a LayeredConfig object for sectionkey already?
            if sectionkey not in self._subsections:
                self._subsections[
                    sectionkey] = LayeredConfig(cascade=self._cascade)
                self._subsections[sectionkey]._sectionkey = sectionkey
                self._subsections[sectionkey]._parent = self

            if self._subsections[sectionkey]._configparser is None:
                self._subsections[
                    sectionkey]._configparser = self._configparser

            self._subsections[sectionkey]._load_inifile_section(sectionkey)
        # return cfgparser

    def _load_inifile_section(self, sectionname):
        for (key, value) in self._configparser.items(sectionname):
            self._inifile[key] = self._type_value(key, value)


class JSONFile(ConfigSource):
    def __init__(self, jsonfile=None, identifier="jsonfile"):
        pass


class Environment(ConfigSource):
    def __init__(self, environ=os.environ, prefix="", lowerize=True, identifier="environment"):
        self.config = None


class Commandline(ConfigSource):
    def __init__(self, argv=sys.argv, identifier="commandline"):
        """
        :param commandline: The contents of sys.argv, or something
                            similar. Any long-style parameters are
                            turned into configuration values, and
                            parameters with hyphens are turned into
                            nested config objects
                            (i.e. ``--module-parameter=foo`` results
                            in self.module.parameter == "foo".
        :type commandline: list
        """
        self.config = None

    # For now: only support long arguments with = separating the parameter and the value, ie
    # "./foo.py --longarg=value" works, "./foo.py --longarg value" or even
    # "./foo.py --longarg = value" doesn't work.
    def _load_commandline(self, commandline):
        if not commandline:
            return
        for arg in commandline:
            if isinstance(arg, bytes):
                arg = arg.decode("utf-8") # FIXME: Find out proper way
                                          # of finding the encoding of
                                          # argv
            if arg.startswith("--"):
                if "=" in arg:
                    (param, value) = arg.split("=", 1)
                else:
                    (param, value) = (arg, True)  # assume bool, not str
                # '--param' => ['param']
                # '--module-param' => ['module','param']
                # Note: Options may not contains hyphens (ie they can't
                # be called "parse-force") since this clashes with hyphen
                # as the sectionkey separator.
                parts = param[2:].split("-")

                self._load_commandline_part(parts, value)

    def _load_commandline_part(self, parts, value):
        if len(parts) == 1:
            key = parts[0]
            if type(value) != bool:  # bools are created implicitly for value-less options
                value = self._type_value(key, value)
            # create a new value, or append to an existing list?
            if key in self._commandline:
                if not isinstance(self._commandline[key], list):
                    self._commandline[key] = [self._commandline[key]]
                self._commandline[key].append(value)
            else:
                self._commandline[key] = value

        else:
            (sectionkey) = parts[0]
            if sectionkey not in self._subsections:
                self._subsections[
                    sectionkey] = LayeredConfig(cascade=self._cascade)
                self._subsections[sectionkey]._sectionkey = sectionkey
                self._subsections[sectionkey]._parent = self
            self._subsections[sectionkey]._load_commandline_part(parts[1:], value)


class LayeredConfig(object):

    def __init__(self, *sources, **kwargs):
        """Creates a config object from zero or more sources.

        If no sources are given, the config object is blank, but you
        can still set values and read them back later.

        Provides unified access to a nested set of configuration
        parameters. The source of these parameters a config file
        (using .ini-file style syntax), command line parameters, and
        default settings embedded in code. Command line parameters
        override configuration file parameters, which in turn override
        default settings in code (hence **Layered** Config).

        Configuration parameters are accessed as regular object
        attributes, not dict-style key/value pairs.  Configuration
        parameter names should therefore be regular python identifiers
        (i.e. only consist of alphanumerical chars and '_').

        Configuration parameter values can be typed (strings,
        integers, booleans, dates, lists...).  Even though ini-style
        config files and command line parameters are by themselves
        non-typed, by specifying default settings in code, parameters
        from a config file or the commamd line can be typed.

        Example::
 
            >>> defaults = {'parameter': 'foo', 'other': 'default'}
            >>> dir = tempfile.mkdtemp()
            >>> inifile = dir + os.sep + "test.ini"
            >>> with open(inifile, "w") as fp:
            ...     res = fp.write("[__root__]\\nparameter = bar")
            >>> argv = ['--parameter=baz']
            >>> conf = LayeredConfig(Defaults(defaults), INIFile(inifile), Commandline(argv))
            >>> conf.parameter == 'baz'
            True
            >>> conf.other == 'default'
            True
            >>> conf.parameter = 'changed'
            >>> conf.other = 'also changed'
            >>> LayeredConfig.write(conf)
            >>> with open(inifile) as fp:
            ...     res = fp.read()
            >>> res == '[__root__]\\nparameter = changed\\nother = also changed\\n\\n'
            True
            >>> os.unlink(inifile)
            >>> os.rmdir(dir)
 
        :param cascade: If an attempt to get a non-existing parameter
                        on a sub (nested) configuration object should
                        attempt to get the parameter on the parent
                        config object. ``False`` by default,
        :type cascade: bool
        :param writable: Whether configuration values should be mutable.
                         ``True`` by default. This does not affect
                         :py:meth:`~Layeredconfig.set`. 
        :type writable: bool
        """
        self._sources = sources
        self._subsections = OrderedDict()
        self._cascade = kwargs.get('cascade', False)
        self._writable = kwargs.get('writable', True)
        self._parent = None
        self._sectionkey = None

        # Each source may have any number of named subsections. We
        # create a LayeredConfig object for each name, and stuff all
        # matching subections from each of our sources in it.
        #
        # 1. find all names
        sectionkeys = []
        for src in self._sources:
            for k in src.subsections():
                if k not in sectionkeys:
                    sectionkeys.append(k)

        for k in sectionkeys:
            # 2. find all subsections in all of our sources
            s = []
            for src in self._sources:
                if k in list(src.subsections()):
                    s.append(src.subsection(k))
            # 3. create a LayeredConfig object for the subsection
            c = LayeredConfig(*s)
            c._sectionkey = k
            self._subsections[k] = c
            
        # cascade=False, writable=True,

    @staticmethod
    def write(config):
        """Configuration parameters can be changed in code. Such changes can
        be written to any write-enabled source (ie. some sort of
        configuration file).
        """
        root = config
        while root._parent:
            root = root._parent
        if root._inifile_dirty:
            with open(root._inifilename, "w") as fp:
                root._configparser.write(fp)

    @staticmethod
    def set(config, key, value, source="defaults"):
        """Sets a value without marking the config file dirty"""
        src = {'defaults': config._defaults,
               'inifile': config._inifile,
               'commandline': config._commandline}[source]
        src[key] = value

    @staticmethod
    def get(config, key, default=None):
        """Works like dict.get."""
        if hasattr(config, key):
            return getattr(config, key)
        else:
            return default

    @staticmethod
    def where(config, key):
        """returns the identifier of a source where a given key is found, or None."""
        pass

    @staticmethod
    def dump(config):
        """Returns the contents of config as a dict."""
        pass

    @staticmethod
    def load(config, d):
        """Recreates a dump()ed config object."""
        pass
        
        
    def __iter__(self):
        l = []
        iterables = [self._commandline.keys(),
                     self._inifile.keys(),
                     self._defaults.keys()]

        if self._cascade and self._parent:
            iterables.append(self._parent)
        
        for k in itertools.chain(*iterables):
            if k not in l:
                l.append(k)
                yield k

    # FIXME: try to use __getattrib__
    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        if name in self._subsections:
            return self._subsections[name]
        for source in self._sources:
            if source.has(name):
                return source.get(name) # optional typing info

        if self._cascade and self._parent:
            return self._parent.__getattribute(name)

        raise AttributeError("Configuration key %s doesn't exist" % name)

    def __setattr__(self, name, value):
        # print("__setattribute__ %s to %s" % (name,value))
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # First make sure that the higher-priority
        # commandline-derived data doesn't shadow the new value.
        if name in self._commandline:
            del self._commandline[name]
        # then update our internal representation
        if name not in self._inifile:
            self._inifile[name] = None
        if value != self._inifile[name]:
            self._inifile[name] = value
            root = self
            while root._parent:
                root = root._parent
            if root._inifilename:
                root._inifile_dirty = True

        # and finally update our associated cfgparser object so that we later
        # can write() out the inifile. This lasts part is a bit complicated as
        # we need to find the root LayeredConfig object where the cfgparser
        # object resides.
        root = self
        sectionkeys = []
        while root._parent:
            # print("root._parent is not None")
            sectionkeys.append(root._sectionkey)
            root = root._parent

        branch = root._configparser
        if branch:
            section = "".join(sectionkeys)  # doesn't really work with more than 1 level
            # print("Setting %s %s %s" % (section,name,str(value)))
            if not section:
                section = "__root__"
            root._configparser.set(section, name, str(value))
        else:
            # If there is no _configparser object, then this
            # LayeredConfig instance was created without one. There is
            # no way to persist configuration values, so we're done
            pass

    def _load_defaults(self, defaults):
        if not defaults:
            return
        for (k, v) in defaults.items():
            if isinstance(v, dict):
                self._subsections[k] = LayeredConfig(
                    defaults=v, cascade=self._cascade)
                self._subsections[k]._sectionkey = k
                self._subsections[k]._parent = self
            else:
                self._defaults[k] = v

    def _load_inifile(self, inifilename):
        if not inifilename:
            self._configparser = None
            return
        if not os.path.exists(inifilename):
            logging.warn("INI file %s does not exist" % inifilename)
            self._configparser = None
            return

        self._configparser = configparser.ConfigParser(dict_type=OrderedDict)
        self._configparser.read(inifilename)

        if self._configparser.has_section('__root__'):
            self._load_inifile_section('__root__')
        for sectionkey in self._configparser.sections():

            # Do we have a LayeredConfig object for sectionkey already?
            if sectionkey not in self._subsections:
                self._subsections[
                    sectionkey] = LayeredConfig(cascade=self._cascade)
                self._subsections[sectionkey]._sectionkey = sectionkey
                self._subsections[sectionkey]._parent = self

            if self._subsections[sectionkey]._configparser is None:
                self._subsections[
                    sectionkey]._configparser = self._configparser

            self._subsections[sectionkey]._load_inifile_section(sectionkey)
        # return cfgparser

    def _type_value(self, key, value):
        """Find appropriate method/class constructor to convert a
           string value to the correct type IF we know the correct
           type."""
        def boolconvert(value):
            # not all bools should be converted, see test_typed_commandline
            if value == "True":
                return True
            elif value == "False":
                return False
            else:
                return value
            
        def listconvert(value):
            # this function is called with both string represenations
            # of entire lists and simple (unquoted) strings. The
            # ast.literal_eval handles the first case, and if the
            # value can't be parsed as a python expression, it is
            # returned verbatim (not wrapped in a list, for reasons)
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError):
                return value

        def datetimeconvert(value):
            try:
                return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        # find the appropriate defaults object. In the case of
        # cascading, could be any parent that has a key key.
        defaults = self._defaults  # base case
        if self._cascade:
            cfg_obj = self
            while cfg_obj is not None:
                if key in cfg_obj._defaults:
                    defaults = cfg_obj._defaults
                    break  # done!
                if hasattr(cfg_obj, '_parent'):
                    cfg_obj = cfg_obj._parent
                else:
                    cfg_obj = None

        if key in defaults:
            if type(defaults[key]) == type:
                # print("Using class for %s" % key)
                t = defaults[key]
            else:
                # print("Using instance for %s" % key)
                t = type(defaults[key])
        else:
            t = str

        if t == bool:
            t = boolconvert
        elif t == list:
            t = listconvert
        elif t == datetime.datetime:
            t = datetimeconvert
        # print("Converting %r to %r" % (value,t(value)))
        return t(value)

    def _load_inifile_section(self, sectionname):
        for (key, value) in self._configparser.items(sectionname):
            self._inifile[key] = self._type_value(key, value)

    # For now: only support long arguments with = separating the parameter and the value, ie
    # "./foo.py --longarg=value" works, "./foo.py --longarg value" or even
    # "./foo.py --longarg = value" doesn't work.
    def _load_commandline(self, commandline):
        if not commandline:
            return
        for arg in commandline:
            if isinstance(arg, bytes):
                arg = arg.decode("utf-8") # FIXME: Find out proper way
                                          # of finding the encoding of
                                          # argv
            if arg.startswith("--"):
                if "=" in arg:
                    (param, value) = arg.split("=", 1)
                else:
                    (param, value) = (arg, True)  # assume bool, not str
                # '--param' => ['param']
                # '--module-param' => ['module','param']
                # Note: Options may not contains hyphens (ie they can't
                # be called "parse-force") since this clashes with hyphen
                # as the sectionkey separator.
                parts = param[2:].split("-")

                self._load_commandline_part(parts, value)

    def _load_commandline_part(self, parts, value):
        if len(parts) == 1:
            key = parts[0]
            if type(value) != bool:  # bools are created implicitly for value-less options
                value = self._type_value(key, value)
            # create a new value, or append to an existing list?
            if key in self._commandline:
                if not isinstance(self._commandline[key], list):
                    self._commandline[key] = [self._commandline[key]]
                self._commandline[key].append(value)
            else:
                self._commandline[key] = value

        else:
            (sectionkey) = parts[0]
            if sectionkey not in self._subsections:
                self._subsections[
                    sectionkey] = LayeredConfig(cascade=self._cascade)
                self._subsections[sectionkey]._sectionkey = sectionkey
                self._subsections[sectionkey]._parent = self
            self._subsections[sectionkey]._load_commandline_part(parts[1:], value)
