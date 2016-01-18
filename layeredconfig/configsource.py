from abc import ABCMeta, abstractmethod
from datetime import date, datetime
import ast
import inspect

from . import LayeredConfig

class ConfigSource(object):
    __metaclass__ = ABCMeta

    identifier = None
    """A string identifying this source, primarily used with
    :py:meth:`LayeredConfig.set`."""

    writable = False
    """Whether or not this source can accept changed configuration
    settings and store them in the same place as the original setting came
    from."""

    dirty = False
    """For writable sources, whether any parameter value in this source
    has been changed so that a call to :py:meth:`save` might be needed."""

    parent = None
    """The parent of this source, if this represents a nested
    configuration source, or None"""

    source = None
    """By convention, this should be your main connection handle, data
     access object, or other resource neededed to retrieve the
     settings."""

    @abstractmethod  # but subclasses should still call it through super()
    def __init__(self, **kwargs):
        """The constructor of the class should set up needed
        resources, such as opening and parsing a configuration file.

        It is a good idea to keep whatever connection handles, data
        access objects, or other resources needed to retrieve the
        settings, as unprocessed as possible. The methods that
        actually need the data (:py:meth:`has`, :py:meth:`get`,
        :py:meth:`subsection`, :py:meth:`subsections` and possibly
        :py:meth:`typed`) should use those resources directly instead
        of reading from cached locally stored copies.

        The constructor must call the superclass'  ``__init__`` method with all
        remaining keyword arguments, ie. ``super(MySource,
        self).__init__(**kwargs)``.

        """
        
        self.identifier = kwargs.get('identifier',
                                     self.__class__.__name__.lower())
        self.writable = kwargs.get('writable', False)
        self.parent = kwargs.get('parent')
        self.source = None

    @abstractmethod
    def has(self, key):
        """This method should return true if the parameter identified by
        ``key`` is present in this configuration source. It is up to
        each configuration source to define the semantics of what
        exactly "is present" means, but a guideline is that only real
        values should count as being present. If you only have some
        sort of placeholder or typing information for ``key`` this
        should probably not return True.

        Note that it is possible that a configuration source would
        return True for ``typed(some_key)`` and at the same time
        return False for ``has(some_key)``, if the source only carries
        typing information, not real values.

        """
        pass # pragma: no cover

    @abstractmethod
    def get(self, key):
        """Should return the actual value of the parameter identified by
        ``key``. If ``has(some_key)`` returns True, ``get(some_key)``
        should always succeed. If the configuration source does not
        include intrinsic typing information (ie. everything looks
        like a string) this method should return the string as-is,
        LayeredConfig is responsible for converting it to the correct
        type."""
        pass # pragma: no cover

    @abstractmethod
    def keys(self): pass  # pragma: no cover

    @abstractmethod
    def typed(self, key):
        """Should return True if this source contains typing information for
        ``key``, ie information about which data type this parameter
        should be. 

        For sources where everything is stored as a string, this
        should generally return False (no way of distinguishing an
        actual string from a date formatted as a string).
        """
        pass # pragma: no cover

    @abstractmethod
    def subsections(self):
        """Should return a list (or other iterator) of subsection keys, ie
        names that represent subsections of this configuration
        source. Not all configuration sources need to support
        subsections. In that case, this should just return an empty
        list.

        """
        pass  # pragma: no cover

    @abstractmethod
    def subsection(self, key):
        """Should return the subsection identified by ``key``, in the form of
        a new object of the same class, but initialized
        differently. Exactly how will depend on the source, but as a
        general rule the same resource handle used as ``self.source``
        should be passed to the new object. Often, the subsection key
        will need to be provided to the new object as well, so that
        :py:meth:`get` and other methods can use it to look in the
        correct place.

        As a general rule, the constructor should be called with a
        ``parent`` parameter set to ``self``.
        """
        pass  # pragma: no cover

    @abstractmethod
    def set(self, key, value):
        """Should set the parameter identified by ``key`` to the new value
        ``value``.

        This method should be prepared for any type of value, ie ints,
        lists, dates, bools... If the backend cannot handle the given
        type, it should convert to a str itself.

        Note that this does not mean that the changes should be
        persisted in the backend data, only in the existing objects
        view of the data (only when :py:meth:`save` is called, the
        changes should be persisted).
        """
        pass  # pragma: no cover

    def setup(self, config):
        """Perform some post-initialization setup. This method will be called
        by the LayeredConfig constructor after its internal initialization is
        finished, with itself as argument. Sources may access all properties
        of the config object in order to eg. find out which parameters have
        been defined.

        The sources will be called in the same order as they were
        provided to the LayeredConfig constructior, ie. lowest
        precedence first.

        :param config: The initialized config object that this source is a part of
        :type config: layeredconfig.LayeredConfig
        """
        pass

    def save(self):

        """Persist changed data to the backend. This generally means to update
        a loaded configuration file with all changed data, or similar.

        This method will only ever be called if :py:data:`writable` is
        True, and only if :py:data:`dirty` has been set to True.

        If your source is read-only, you don't have to implement this method.
        """
        pass 

    # @abstractmethod
    # should this be called "coerce", "cast" or something similar
    def typevalue(self, key, value):
        """Given a parameter identified by ``key`` and an untyped string,
        convert that string to the type that our version of key has.

        """

        def listconvert(value):
            # this function might be called with both string
            # represenations of entire lists and simple (unquoted)
            # strings. String representations come in two flavours,
            # the (legacy/deprecated) python literal (eg "['foo',
            # 'bar']") and the simple (eg "foo, bar") The
            # ast.literal_eval handles the first case, and if the
            # value can't be parsed as a python expression, the second
            # way is attempted. If both fail, it is returned verbatim
            # (not wrapped in a list, for reasons)
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError):
                if "," in value:
                    return [x.strip() for x in value.split(",")]
                else:
                    return value

        # self.get(key) should never fail
        default = self.get(key)
        # if type(default) == type:
        if inspect.isclass(default):
            # print("Using class for %s" % key)
            t = default
        else:
            # print("Using instance for %s" % key)
            t = type(default)

        if t == bool:
            t = LayeredConfig.boolconvert
        elif t == list:
            t = listconvert
        elif t == date:
            t = LayeredConfig.dateconvert
        elif t == datetime:
            t = LayeredConfig.datetimeconvert
        # print("Converting %r to %r" % (value,t(value)))
        return t(value)

    # Internal function for now, until we find a generalized
    # extensible way of handling type conversions
    def _strvalue(self, value):
        if isinstance(value, list): # really any iterable but not
            # strings...  if any of the elements contain " " or ", "
            # use literal syntax, otherwise use simple syntax
            if [x for x in value if " " in x or "," in x]:
                # can't use repr or str because unicode strings on py2
                # will result in a literal like "[u'foo', u'bar']", we
                # want "[u'foo', u'bar']"
                return "[%s]" % ", ".join(["'"+x.replace("'", "\'")+"'" for x in value])
            else:
                return ", ".join(value)
        else:
            return str(value)
