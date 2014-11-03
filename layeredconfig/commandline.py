from collections import defaultdict
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict
from six import text_type as str
import sys
from copy import copy

from . import ConfigSource

class Commandline(ConfigSource):

    rest = []
    """The remainder of the command line, containing all parameters that
    couldn't be turned into configuration settings. """
    
    def __init__(self,
                 commandline=None,
                 sectionsep="-",
                 **kwargs):
        """Load configuration from command line options. Any long-style
        parameters are turned into configuration values, and
        parameters containing the section separator (by default
        ``"-"``) are turned into nested config objects
        (i.e. ``--module-parameter=foo`` results in
        ``self.module.parameter == "foo"``.

        :param commandline: Command line arguments, in list form like
                            :py:data:`sys.argv`. If not provided, uses
                            the real :py:data:`sys.argv`.
        :type  commandline: list
        :param sectionsep: An alternate section separator instead of ``-``.
        :type  sectionsep: str

        """
        super(Commandline, self).__init__(**kwargs)
        if commandline is None:
            if kwargs.get("empty"):
                commandline = []
            else:
                commandline = sys.argv
        self.source = OrderedDict()
        self.sectionargvs = defaultdict(list)
        self.sectionsep = sectionsep
        self.rest = []
        for arg in commandline:
            if isinstance(arg, bytes):
                # FIXME: Find out proper way of finding the encoding
                # of argv
                arg = arg.decode("utf-8") 
            if arg.startswith("--"):
                if "=" in arg:
                    (param, value) = arg.split("=", 1)
                else:
                    (param, value) = (arg, True)  # assume bool, not str
                # '--param' => ['param']
                # '--module-param' => ['module','param']
                # Note: parameter names may not contain sectionsep (ie
                # they can't be called "parse-force").
                parts = param[2:].split(sectionsep)
                self._load_commandline_part(parts, value, self.sectionargvs)
            else:
                self.rest.append(arg)

    def _load_commandline_part(self, parts, value, sectionargvs):
        if len(parts) == 1:
            key = parts[0]
            if key in self.source:
                if not isinstance(self.source[key], list):
                    self.source[key] = [self.source[key]]
                self.source[key].append(value)
            else:
                self.source[key] = value
        else:
            (sectionkey) = parts[0]
            # recreate the cmdline -- note that this will turn
            # valueless options into explicit, ie "--foo" =>
            # "--foo=True"
            arg = "--%s=%s" % (self.sectionsep.join(parts[1:]), value)
            sectionargvs[sectionkey].append(arg)

    def subsections(self):
        return self.sectionargvs.keys()
        
    def subsection(self, key):
        return Commandline(self.sectionargvs[key],
                           parent=self,
                           identifier=self.identifier)

    def has(self, k):
        return k in self.source

    def get(self, k):
        # FIXME: run self_type_value using a type information source
        # that we somehow have access to.
        return self.source[k]

    def set(self, k, v):
        self.source[k] = v
       
    def keys(self):
        return self.source.keys()  # or "for k in self.source: yield k"
        # what about subsections?

    def typed(self, key):
        # if the value is anything other than a string, we can be sure
        # that it contains useful type information (eg bool, list)
        try:
            return not isinstance(self.get(key), str)
        except:
            return False
