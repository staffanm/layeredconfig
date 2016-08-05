import codecs
import logging
import os
import sys
import six
from six.moves import configparser
from six import text_type as str
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict

from . import ConfigSource


class INIFile(ConfigSource):
    def __init__(self,
                 inifilename=None,
                 rootsection="__root__",
                 writable=True, 
                 **kwargs):
        """Loads and optionally saves configuration files in INI format, as
        handled by :py:mod:`configparser`.

        :param inifile: The name of a ini-style configuration
                        file. The file should have a top-level
                        section, by default named ``__root__``, whose
                        keys are turned into top-level configuration
                        parameters. Any other sections in this file
                        are turned into nested config objects.
        :type inifile: str
        :param rootsection: An alternative name for the top-level section. 
                            See note below. 
        :type rootsection: str
        :param writable: Whether changes to the LayeredConfig object
                         that has this INIFile object amongst its
                         sources should be saved in the INI file.
        :type writable: bool

        .. note::

           Since this source uses :py:mod:`configparser`, and since
           that module handles sections named ``[DEFAULT]``
           differently, this module will have a sort-of automatic
           cascading feature for subsections if ``DEFAULT`` is used as
           ``rootsection``

        """
        super(INIFile, self).__init__(**kwargs)
        if inifilename:
            if not os.path.exists(inifilename):
                logging.warning("INI file %s does not exist" % inifilename)
                # create a empty RawConfigParser (Raw to avoid the
                # interpolation behaviour of other classes)
                self.source = configparser.RawConfigParser(dict_type=OrderedDict)
                self.inifilename = inifilename
                if rootsection != "DEFAULT":
                    self.source.add_section(rootsection)
            else:
                self.source = configparser.RawConfigParser(dict_type=OrderedDict)
                if sys.version_info >= (3,2):
                    reader = self.source.read_file
                else:
                    reader = self.source.readfp
                # we don't know the encoding of this file; assume utf-8
                with codecs.open(inifilename, encoding="utf-8") as fp:
                    reader(fp)
                
                self.inifilename = inifilename
        # only used when creating new INIFile objects internally
        elif 'config' in kwargs:  
            self.source = kwargs['config']
            self.inifilename = None
        else:
            # This is an "empty" INIFile object
            self.source = configparser.ConfigParser(dict_type=OrderedDict)
            self.source.add_section(rootsection)
            self.inifilename = None
        if 'section' in kwargs:
            self.sectionkey = kwargs['section']
        else:
            self.sectionkey = rootsection
            self.dirty = False
        self.writable = writable
        self.rootsection = rootsection

    def typed(self, key):
        # INI files carry no intrinsic type information
        return False

    def subsections(self):
        # self.source may be None if we provided the path to a
        # nonexistent inifile (this should probably throw an exception
        # instead)
        if not self.source:
            return []
        elif self.sectionkey != self.rootsection:
            # sections can't be nested using configparser
            return []
        else:
            return [x for x in self.source.sections() if x != self.rootsection]

    def subsection(self, key):
        return INIFile(config=self.source, section=key,
                       parent=self, identifier=self.identifier)

    def has(self, key):
        if self.sectionkey == "DEFAULT":
            return key in self.source.defaults()
        else:
            return self.source.has_option(self.sectionkey, key)

    def get(self, key):
        return str(self.source.get(self.sectionkey, key))

    def set(self, key, value):
        self.source.set(self.sectionkey, key, self._strvalue(value))

    def keys(self):
        for k in self.source.options(self.sectionkey):
            yield k

    def save(self):
        # this should only be called on root objects
        assert not self.parent, "save() should only be called on root objects"
        if self.inifilename:
            with open(self.inifilename, "w") as fp:
                self.source.write(fp)
