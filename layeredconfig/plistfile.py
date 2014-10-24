import plistlib

from . import DictSource

class PListFile(DictSource):
    def __init__(self, plistfile, writable=True, identifier="plist"):
        super(JSONFile, self).__init__()
        with open(plistfile, "rb") as fp:
            self.source = plistlib.load(fp)
        self.writable = writable
        self.identifier = identifier
