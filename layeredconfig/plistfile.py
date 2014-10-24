import plistlib

from . import DictSource

class PListFile(DictSource):
    def __init__(self, plistfile=None, writable=True, *args, **kwargs):
        super(PListFile, self).__init__(*args, **kwargs)
        if 'defaults' in kwargs:
            self.source = defaults
        else:
            with open(plistfile, "rb") as fp:
                self.source = plistlib.load(fp)
            self.plistfile = plistfile
