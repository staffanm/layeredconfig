# this should possibly be a abstract class as well
from . import ConfigSource

class DictSource(ConfigSource):
    def __init__(self):
        super(DictSource, self).__init__()
        self.source = {}

    def subsections(self):
        for (k, v) in self.source.items():
            if isinstance(v, dict):
                yield k

    def keys(self):
        for (k, v) in self.source.items():
            if not isinstance(v, dict):
                yield k

    def subsection(self, key):
        # FIXME: File-based DictSource subclasses (JSONFile and
        # YAMLFile must be adapted to accept a sub-dict in place of a
        # filename
        return self.__class__(self.source[key])

    def typed(self, key):
        return True

    def has(self, key):
        # should has return true for types or only for real values?
        return key in self.source and not isinstance(self.source[key], type)

    def get(self, key):
        return self.source[key]

    def set(self, key, value):
        self.source[key] = value
