import plistlib

from . import DictSource

class PListFile(DictSource):
    def __init__(self, plistfile=None, writable=True, identifier="plist", **kwargs):
        super(PListFile, self).__init__()
        if 'defaults' in kwargs:
            self.source = defaults
        else:
            with open(plistfile, "rb") as fp:
                self.source = plistlib.load(fp)
            self.plistfile = plistfile
        self.writable = writable
        self.identifier = identifier
