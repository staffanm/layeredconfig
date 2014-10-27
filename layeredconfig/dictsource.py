# this should possibly be a abstract class as well
from . import ConfigSource

class DictSource(ConfigSource):
    def __init__(self, *args, **kwargs):
        super(DictSource, self).__init__(*args, **kwargs)
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
        return key in self.source        


    def has(self, key):
        # should has return true for types or only for real values?
        return key in self.source and not isinstance(self.source[key], type)

    def get(self, key):
#        if key in self.source:
        return self.source[key]
#        elif self.cascade and self.parent:
#            return self.parent.get(key)
#        else:
#            # crash and burn -- we know that key WON'T be in self.source
#            self.source[key]

    def set(self, key, value):
        self.source[key] = value
