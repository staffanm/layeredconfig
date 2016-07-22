# this should possibly be a abstract class as well
from . import ConfigSource


class DictSource(ConfigSource):
    def __init__(self, **kwargs):
        """If your backend data is exposable as a python dict, you can
        subclass from this class to avoid implementing :py:meth:`has`,
        :py:meth:`get`, :py:meth:`keys`, :py:meth:`subsection` and
        :py:meth:`subsections`. You only need to write
        :py:meth:`__init__` (which should set ``self.source`` to that
        exposed dict), and possibly :py:meth:`typed` and
        :py:meth:`save`.

        """
        super(DictSource, self).__init__(**kwargs)
        self.source = {}

    def subsections(self):
        for (k, v) in self.source.items():
            if isinstance(v, dict):
                yield k

    def keys(self):
        for (k, v) in self.source.items():
            if not isinstance(v, dict) and not isinstance(v, type):
                yield k

    def subsection(self, key):
        # Make an object of the correct type
        return self.__class__(defaults=self.source[key],
                              parent=self,
                              identifier=self.identifier)

    def typed(self, key):
        # if we have it, we can type it
        return key in self.source and self.source[key] is not None

    def has(self, key):
        # should has return true for types or only for real values?
        return key in self.source and not isinstance(self.source[key], type)

    def get(self, key):
        return self.source[key]

    def set(self, key, value):
        self.source[key] = value
