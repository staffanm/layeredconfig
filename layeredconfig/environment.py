from . import ConfigSource

class Environment(ConfigSource):
    def __init__(self,
                 environ=None,
                 prefix="",
                 sectionsep="_",
                 *args,
                 **kwargs):
        super(Environment, self).__init__(*args, **kwargs)
        if not environ:
            environ = os.environ
        self.source = environ
        self.prefix = prefix
        self.sectionsep = sectionsep

    # used by both keys and subsections, but in different ways
    def _internalkeys(self):
        return  [x.lower()[len(self.prefix):] for x in self.source.keys()]
        
    def keys(self):
        for x in self._internalkeys():
            if self.sectionsep not in x:
                yield x

    def has(self, key):
        # reverse the prefix/lowerize stuff
        k = self.prefix + key.upper()
        return k in self.source

    def get(self, key):
        k = self.prefix + key.upper()
        return self.source[k]

    def set(self, key, val):
        k = self.prefix + key.upper()
        self.source[k] = val

    def typed(self, key):
        return False

    def subsections(self):
        yielded = set()
        for x in self._internalkeys():
            if self.sectionsep in x:
                section = x.split(self.sectionsep)[0]
                if section not in yielded:
                    yield(section)
                    yielded.add(section)

    def subsection(self, key):
        s = key.upper() + self.sectionsep
        newenviron = dict([(k.replace(s,"", 1), v) for k, v in self.source.items() if s in k])
        return Environment(newenviron,
                           prefix=self.prefix,
                           sectionsep=self.sectionsep,
                           parent=self,
                           identifier=self.identifier)
