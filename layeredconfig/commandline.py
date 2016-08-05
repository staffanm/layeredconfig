import sys
import argparse

from six import text_type as str

from . import ConfigSource

class Commandline(ConfigSource):

    rest = []
    """The remainder of the command line, containing all parameters that
    couldn't be turned into configuration settings. """

    def __init__(self,
                 commandline = None,
                 parser=None,
                 sectionsep='-',
                 add_help=True, 
                 **kwargs):
        """Load configuration from command line options. Any long-style
        parameters are turned into configuration values, and
        parameters containing the section separator (by default
        ``"-"``) are turned into nested config objects
        (i.e. ``--module-parameter=foo`` results in
        ``self.module.parameter == "foo"``.

        If an initialized ArgumentParser object is provided, the
        defined parameters in that object is used for supporting short
        form options (eg. ``'-f'`` instead of ``'--force'``), typing
        information and help text. The standards argparse feature of
        printing a helpful message when the '-h' option is given is
        retained.

        :param commandline: Command line arguments, in list form like
                            :py:data:`sys.argv`. If not provided, uses
                            the real :py:data:`sys.argv`.
        :type  commandline: list
        :param parser: An initialized/configured argparse object
        :type  parser: argparse.ArgumentParser
        :param sectionsep: An alternate section separator instead of ``-``.
        :type  sectionsep: str
        :param add_help: Same as for ArgumentParser()
        :type  add_help: bool

        """
        # internal arguments:
        # * sectionkey: eg 'mymodule' or 'submodule_subsubmodule' etc
        super(Commandline, self).__init__(**kwargs)
        self.sectionsep = sectionsep
        self.sectionkey = kwargs.get('sectionkey', '') 
        if commandline is None:
            if kwargs.get("empty"):
                self.commandline = []
            else:
                self.commandline = sys.argv[1:]
        else:
            self.commandline = commandline
        self.autoargs = kwargs.get('autoargs', {})
        if parser is None:
            if kwargs.get('parent'):
                # we're a subsection object, we don't need a parser. 
                self.parser = None
            else:
                # create a "bootstrapping" argument parser
                self.parser = argparse.ArgumentParser()
                for arg in self.commandline:
                    if arg.startswith("--"):
                        argname = arg.split("=")[0][2:]
                        if argname not in self.autoargs:
                            # at this point we don't know anything about
                            # this argument other than that it exists and
                            # our bootstrapping argument parser should
                            # handle it.
                            # * use nargs='?' to allow arguments with or without
                            #   values.
                            # * use const=True to treat valueless arguments as
                            #   set bool flags
                            # * use action='append' to allow a single argument
                            #   (eg --extra) to be used multiple times with values)
                            self.parser.add_argument("--%s" % argname,
                                                     action='append',
                                                     nargs='?',
                                                     const=True)
                            self.autoargs[argname] = True
            self._provided_parser = False
        else:
            self.parser = parser
            self._provided_parser = kwargs.get('provided_parser', True)
        self.writable = False
        # create a (possibly temporary) source (argparse.Namespace object)
        # unless we're a subsection object and already have been passed one.
        if kwargs.get('parent'):
            self.source = None # or {} ?
        else:
            if kwargs.get('source'):
                self.source = kwargs['source']
            else:
                self.source, self.rest = self.parser.parse_known_args(self.commandline)
        if self._provided_parser and self.rest:
            # reconfigure our provided parser and try to add arguments
            # for every unprocessed long option.
            for arg in self.rest:
                if arg.startswith("--"):
                    argname = arg.split("=")[0][2:]
                    if (argname not in self.autoargs and
                        argname not in self.source):
                        self.parser.add_argument("--%s" % argname,
                                                 action='append',
                                                 nargs='?',
                                                 const=True)
                        self.autoargs[argname] = True
            # now redo the parsing
            self.source, self.rest = self.parser.parse_known_args(self.commandline)

    def setup(self, config):
        if not self.parser:
            # we're in an empty subsection object
            return 
        for key in config:
            # since this will be used to handle -h, we need to fill it
            # with helpy things (default types, default values, help strings)
            try:
                currentval = getattr(config, key)
                if currentval:
                    currenttype = type(currentval)
                    # select a good converter for string -> type
                    kwargs = {'type': currenttype}
                else:
                    kwargs = {}

                if key not in self.source:
                    self.parser.add_argument('--%s' % key,
                                             action='append',
                                             nargs='?',
                                             const=True,
                                             **kwargs)
                    self.autoargs[key] = True
            except argparse.ArgumentError:
                # the parser already had this argument -- assume it's
                # fully configured with typing, help, and
                # everything. But it'd be nice if we could jam a
                # default value in there somehow
                pass
        # process everything and print help if -h is given
        self.source, self.rest = self.parser.parse_known_args(self.commandline)

    def keys(self):
        if self.source:
            for arg in vars(self.source).keys():
                if arg.startswith(self.sectionkey) and getattr(self.source, arg) is not None:
                    k = arg[len(self.sectionkey):]
                    if k.startswith("_"):
                        k = k[1:]
                    if "_" not in k and getattr(self.source, arg) is not None:
                        yield k

    def has(self, key):
        if self.sectionkey:
            key = self.sectionkey + "_" + key
        try:
            return getattr(self.source, key) is not None
        except AttributeError:
            return False

    def get(self, key):
        if self.sectionkey:
            key = self.sectionkey + "_" + key
        r = getattr(self.source, key)
        # undo the automatic list behaviour for autodiscovered
        # arguments (which has store='append')
        if (key.replace("_", "-") in self.autoargs and
            isinstance(r, list) and len(r) == 1):
            return r[0]
        else:
            return r

    def subsections(self):
        # argparse has no internal concept of subsections. We
        # construct one using arguments like '--mymodule-force'. These
        # are transformed into attributes like 'mymodule_force' on an
        # argparse.Namespace object. Therefore, we can create a list
        # of subsections
        yielded = set()
        for args in dict(self.source._get_kwargs()).keys():
            if args.startswith(self.sectionkey):
                args = args[len(self.sectionkey):]
                if args.startswith("_"): # sectionsep
                    args = args[1:]
            else:
                continue
            # '_' is the hardcoded section separator once parse_args
            # has transformed the command line args into properties on
            # a Namespace object.
            if "_" in args:
                section = args.split("_")[0]
                if section not in yielded:
                    yield(section)
                    yielded.add(section)

    def subsection(self, key):
        if self.sectionkey:
            key = self.sectionkey + "_" + key
        
        return Commandline(self.commandline,
                           source=self.source,
                           parser=self.parser,
                           provided_parser=self._provided_parser,
                           autoargs=self.autoargs,
                           sectionkey=key)

    def set(self, key, value):
        setattr(self.source, key, value)

    def typed(self, key):
        # if the config value has a non-string type, then it's typed
        if self.has(key) and not isinstance(self.get(key), str):
            return True

        if self._provided_parser:
            # a provided parser (not a bootstrapped parser) should be
            # able to convert input to typed data -- but only for
            # those arguments that were configured
            return self.has(key) and key not in self.autoargs
        else:
            # a boostrapped parser will support typing for bool
            # (valueless args) and lists (multiple args)
            return self.has(key) and not isinstance(self.get(key), str)


