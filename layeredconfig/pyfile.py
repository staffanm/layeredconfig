import six
from . import ConfigSource

import inspect

class PyFile(ConfigSource):

    def __init__(self, pyfilename=None, **kwargs):
        """Loads configuration from a python source file. Any variables
        defined in that file will be interpreted as configuration
        keys. The class ``Subsection`` is automatically imported into
        the context when the file is executed, and represents a
        subsection of the configuration. Any attribute set on such an
        object is treated as a configuration parameter on that
        subsection.

        .. note::

           The python source file is loaded and interpreted once, when
           creating the PyFile object. If a value is set by
           eg. calling a function, that function will only be called
           at load time, not when accessing the parameter.

        :param pyfile: The name of a file containing valid python code.
        :type pyfile: str

        """
        super(PyFile, self).__init__(**kwargs)
        self.source = Subsection()
        if pyfilename:
            with open(pyfilename) as fp:
                pycode = compile(fp.read(), pyfilename, 'exec')
            six.exec_(pycode, globals(), self.source)
        elif kwargs.get('dict'):
            self.source = kwargs['dict']
        
    def has(self, key):
        return key in self.source and not isinstance(key, Subsection)

    def get(self, key):
        return self.source.get(key)

    def keys(self):
        for key, val in self.source.items():
            if not (isinstance(val, Subsection) or
                    inspect.ismodule(val) or
                    inspect.isfunction(val) or
                    val.__class__.__module__ in ('__future__')):
                yield key

    def subsections(self):
        return [key for key in self.source.keys() if isinstance(self.source[key], Subsection)]

    def subsection(self, key):
        # wrap this somehow?
        return PyFile(pyfilename=None, dict=self.source.get(key))

    def set(self, key, value):
        # as self.writable is False, this will never be called
        return ValueError("Cannot set variables in a pyfile")
    
    def typed(self, key):
        # if we have it, it's typed
        return self.has(key)

class Subsection(dict):
    # pass

    # to allow subsect.key = value syntax, but still store data in
    # self, not self.__dict__
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        return self[key]
