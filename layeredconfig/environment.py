import os

from . import ConfigSource

class Environment(ConfigSource):
    def __init__(self,
                 environ=None,
                 prefix=None,
                 lower=True,
                 sectionsep="_",
                 **kwargs):
        """Loads settings from environment variables. If ``prefix`` is set to
        ``MYAPP_``, the value of the environment variable ``MYAPP_HOME``
        will be available as the configuration setting ``home``.

        :param environ: Environment variables, in dict form like
                        :py:data:`os.environ`. If not provided, uses
                        the real :py:data:`os.environ`.
        :type environ: dict
        :param prefix: Since the entire environment is not suitable to use
                       as a configuration, only variables starting with this
                       prefix are used.
        :type prefix:  str
        :param lower: If true, lowercase the name of environment
                      variables (since these typically uses uppercase)
        :type  lower: True

        """
        super(Environment, self).__init__(**kwargs)
        if environ is None:
            if kwargs.get("empty"):
                environ = {}
            else:
                environ = os.environ
        if prefix is None:
            prefix = ""
        
        self.source = environ
        self.prefix = prefix
        self.sectionsep = sectionsep

    # used by both keys and subsections, but in different ways
    def _internalkeys(self):
        return  [x.lower()[len(self.prefix):] for x in self.source.keys() if x.startswith(self.prefix)]
        
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
