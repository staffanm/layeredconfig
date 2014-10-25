from abc import ABCMeta, abstractmethod
from datetime import date, datetime
import ast

class ConfigSource(object):
    __metaclass__ = ABCMeta

    @abstractmethod  # but subclasses should still call it through super()
    def __init__(self, *args, **kwargs):
        self.identifier = kwargs.get('identifier',
                                     self.__class__.__name__.lower())
        self.writable = kwargs.get('writable', False)
        self.cascade = kwargs.get('cascade', False)
        self.parent = kwargs.get('parent')
        self.source = None

    @abstractmethod
    def typed(self, key):
        return

    # @abstractmethod
    # should this be called "coerce", "cast" or something similar
    def typevalue(self, key, value):
        """Given a option key and an untyped string, convert that string to
        the type that our version of key has.

        """

        def boolconvert(value):
            # not all bools should be converted, see test_typed_commandline
            if value == "True":
                return True
            elif value == "False":
                return False
            else:
                return value
            
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

        def datetimeconvert(value):
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        def dateconvert(value):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%d").date()

        # self.get(key) should never fail
        default = self.get(key)
        if type(default) == type:
            # print("Using class for %s" % key)
            t = default
        else:
            # print("Using instance for %s" % key)
            t = type(default)

        if t == bool:
            t = boolconvert
        elif t == list:
            t = listconvert
        elif t == date:
            t = dateconvert
        elif t == datetime:
            t = datetimeconvert
        # print("Converting %r to %r" % (value,t(value)))
        return t(value)

    @abstractmethod
    def subsections(self):
        return

    @abstractmethod
    def subsection(self, key):
        return

    @abstractmethod
    def has(self, key):
        return

    @abstractmethod
    def get(self, key):
        return

    @abstractmethod
    def set(self, key, value):
        return

    @abstractmethod
    def keys(self):
        return

