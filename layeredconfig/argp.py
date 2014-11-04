import argparse

from . import ConfigSource

class Argparser(ConfigSource):

    def __init__(self,
                 parser=None,
                 commandline = None,
                 **kwargs):
        """Load configuration from a argparse object, or construct a argparse
        object from other sources

        :param parser: An initialized/configured argparse object
        :type  parser: argparse.ArgumentParser
        :param commandline: Command line arguments, in list form like
                            :py:data:`sys.argv`. If not provided, uses
                            the real :py:data:`sys.argv`.
        :type  commandline: list
        :param sectionsep: An alternate section separator instead of ``-``.
        :type  sectionsep: str

        """
        super(Argparser, self).__init__(**kwargs)
        if parser is None:
            self.source = argparse.ArgumentParser()
        else:
            self.source = parser
        if commandline is None:
            self.commandline = sys.argv
        else:
            self.commandline = commandline
        self.writable = False
        self.args = None

    def setup(self, config):
        """(Re-)initialize the parser"""

        for key in config:
            # since this will be used to handle -h, we need to fill it
            # with helpy things
            self.source.add_argument('--%s' % key,
                                     type=get_type(key),
                                     help=get_help(key))

        # process everything and print help if -h is given
        self.args = self.source.parse_args(self.commandline)

    def keys(self):
        if self.args:
            for arg in self.args:
                yield arg

    def has(self, key):
        pass

    def get(self, key):
        pass

    def subsections(self):
        # argparse has no concept of subsections
        return []

    def subsection(self):
        raise NotImplementedError  # pragma: no cover

    def set(self, key, value):
        raise NotImplementedError

    def typed(self, key):
        return False
