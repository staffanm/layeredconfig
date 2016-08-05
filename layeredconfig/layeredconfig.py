# -*- coding: utf-8 -*-

import itertools
import logging
from datetime import datetime, date

try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict


class LayeredConfig(object):
    def __init__(self, *sources, **kwargs):
        """Creates a config object from one or more sources and provides
        unified access to a nested set of configuration
        parameters. The source of these parameters a config file
        (using .ini-file style syntax), command line parameters, and
        default settings embedded in code. Command line parameters
        override configuration file parameters, which in turn override
        default settings in code (hence **Layered** Config).

        Configuration parameters are accessed as regular object
        attributes, not dict-style key/value pairs.  Configuration
        parameter names should therefore be regular python
        identifiers, and preferrably avoid upper-case and "_" as well
        (i.e. only consist of the characters a-z and 0-9)

        Configuration parameter values can be typed (strings,
        integers, booleans, dates, lists...). Even though some sources
        lack typing information (eg in INI files, command-line
        parameters and enviroment variables, everything is a string),
        LayeredConfig will attempt to find typing information in other
        sources and convert data.

        :param \*sources: Initialized ConfigSource-derived objects
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
            try:
                for k in src.subsections():
                    if k not in sectionkeys:
                        sectionkeys.append(k)
            except AttributeError:  # possibly others, or all
                # we couldn't get any subsections for source, perhaps
                # because it's an "empty" source. Well, that's ok.
                pass

        for k in sectionkeys:
            # 2. find all subsections in all of our sources
            s = []
            for src in self._sources:
                if k in list(src.subsections()):
                    s.append(src.subsection(k))
                else:
                    # create an "empty" subsection object. It's
                    # important that all the LayeredConfig objects in a
                    # tree have the exact same set of
                    # ConfigSource-derived types.
                    # print("creating empty %s" % src.__class__.__name__)
                    s.append(src.__class__(parent=src,
                                           identifier=src.identifier,
                                           writable=src.writable,
                                           empty=True,
                                           cascade=self._cascade))
            # 3. create a LayeredConfig object for the subsection
            c = self.__class__(*s,
                               cascade=self._cascade,
                               writable=self._writable)
            c._sectionkey = k
            c._parent = self
            self._subsections[k] = c

        # 4. give each source a chance to to some post-init setup.
        for src in self._sources:
            src.setup(self)

    @staticmethod
    def write(config):
        """Commits any pending modifications, ie save a configuration file if
        it has been marked "dirty" as a result of an normal
        assignment. The modifications are written to the first
        writable source in this config object.

        .. note::

           This is a static method, ie not a method on any object
           instance. This is because all attribute access on a
           LayeredConfig object is meant to retrieve configuration
           settings.

        :param config: The configuration object to save
        :type  config: layeredconfig.LayeredConfig

        """
        root = config
        while root._parent:
            root = root._parent

        for source in root._sources:
            if source.writable and source.dirty:
                source.save()

    @staticmethod
    def set(config, key, value, sourceid="defaults"):
        """Sets a value in this config object *without* marking any source
        dirty, and with exact control of exactly where to set the
        value. This is mostly useful for low-level trickery with
        config objects.

        :param config: The configuration object to set values on
        :param key: The parameter name
        :param value: The new value
        :param sourceid: The identifier for the underlying source that the
                         value should be set on.
        """
        for source in config._sources:
            if source.identifier == sourceid:
                source.set(key, value)
                # What if no source is found? We silently ignore...

    @staticmethod
    def get(config, key, default=None):
        """Gets a value from the config object, or return a default value if
        the parameter does not exist, like :py:meth:`dict.get` does.
        """

        if hasattr(config, key):
            return getattr(config, key)
        else:
            return default

    @staticmethod
    def dump(config):
        """Returns the entire content of the config object in a way that can
        be easily examined, compared or dumped to a string or file.

        :param config: The configuration object to dump
        :rtype: dict

        """
        def _dump(element):
            if not isinstance(element, config.__class__):
                return element

            section = dict()
            for key, subsection in element._subsections.items():
                section[key] = _dump(subsection)
            for key in element:
                section[key] = getattr(element, key)
            return section

        return _dump(config)

    # These are methods i'd like to implement next
    #
    #    @staticmethod
    #    def where(config, key):
    #        """returns the identifier of a source where a given key is found, or None."""
    #        pass
    #
    #    @staticmethod
    #    def load(config, d):
    #        """Recreates a dump()ed config object."""
    #        pass

    @staticmethod
    def datetimeconvert(value):
        """Convert the string *value* to a :py:class:`~datetime.datetime`
        object. *value* is assumed to be on the form "YYYY-MM-DD
        HH:MM:SS" (optionally ending with fractions of a second).

        """
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def dateconvert(value):
        """Convert the string *value* to a :py:class:`~datetime.date`
        object. *value* is assumed to be on the form "YYYY-MM-DD".

        """
        return datetime.strptime(value, "%Y-%m-%d").date()

    @staticmethod
    def boolconvert(value):
        """Convert the string *value* to a boolean. ``"True"`` is converted to
        ``True`` and ``"False"`` is converted to ``False``.

        .. note::

           If value is neither "True" nor "False", it's returned unchanged.

        """
        # not all bools should be converted, see test_typed_commandline
        if value == "True":
            return True
        elif value == "False":
            return False
        else:
            return value

    def __repr__(self):
        return self.dump(self).__repr__()

    def __iter__(self):
        l = set()

        iterables = [x.keys() for x in self._sources]

        if self._cascade:
            c = self
            while c._parent:
                iterables.append(c._parent)
                c = c._parent

        for k in itertools.chain(*iterables):
            if k not in l:
                l.add(k)
                yield k

    def __getattr__(self, name):

        if name in self._subsections:
            return self._subsections[name]

        found = False
        # find the appropriate value in the highest-priority source
        for source in reversed(self._sources):
            # if self._cascade, we must climb the entire chain of
            # .parent objects to be sure.
            done = False
            while not done:
                if source.has(name):
                    found = True
                    done = True  # we found it
                elif self._cascade and source.parent:
                    source = source.parent
                else:
                    done = True  # we didn't find it
            if found:
                break

        if found:
            if source.typed(name):
                return source.get(name)
            else:
                # we need to find a typesource for this value.
                done = False
                this = self
                while not done:
                    for typesource in reversed(this._sources):
                        if typesource.typed(name):
                            done = True
                            break
                    if not done and self._cascade and this._parent:
                        # Iterate up the parent chain to find it.
                        this = this._parent
                    else:
                        done = True

                if typesource.typed(name):
                    return typesource.typevalue(name, source.get(name))
                else:
                    # we can't type this data, return as-is
                    return source.get(name)
        else:
            if self._cascade and self._parent:
                return self._parent.__getattr__(name)

        raise AttributeError("Configuration key %s doesn't exist" % name)

    def __setattr__(self, name, value):
        # print("__setattribute__ %s to %s" % (name,value))
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # we need to get access to two sources:

        # 1. the highest-priority writable source (regardless of
        #    whether it originally had this value)
        found = False
        for writesource in reversed(self._sources):
            if writesource.writable:
                found = True
                break
        if found:
            writesource.set(name, value)
            writesource.dirty = True
            while writesource.parent:
                writesource = writesource.parent
                writesource.dirty = True

        # 2. the highest-priority source that has this value (typed or
        # not) or contains typing info for it.
        found = False
        for source in reversed(self._sources):
            if source.has(name) or source.typed(name):
                found = True
                break
        if found:
            source.set(name, value)  # regardless of typing
        elif self._cascade and self._parent:
            return self._parent.__setattr__(name, value)
        else:
            raise AttributeError("Configuration key %s doesn't exist" % name)
