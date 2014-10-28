import plistlib
from datetime import datetime

from six import text_type as str
from six import binary_type as bytes

from . import DictSource


class PListFile(DictSource):
    def __init__(self, plistfilename=None, writable=True, *args, **kwargs):
        super(PListFile, self).__init__(*args, **kwargs)
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        else:
            with open(plistfilename, "rb") as fp:
                self.source = plistlib.readPlist(fp)
            self.plistfilename = plistfilename
            self.dirty = False
        self.encoding = "utf-8"  # I hope this is a sensible default
        self.writable = writable
        
    def set(self, key, value):
        # plist natively supports some types but not all (notably not date)
        if not isinstance(key, (str, bool, int, list, datetime)):
            value = str(value)
        super(PListFile, self).set(key, value)

    def get(self, key):
        ret = super(PListFile, self).get(key)
        if isinstance(ret, bytes):
            ret = ret.decode(self.encoding)
        return ret

    def save(self):
        assert not self.parent, "save() should only be called on root objects"
        if self.plistfilename:
            with open(self.plistfilename, "w") as fp:
                plistlib.writePlist(self.source, fp)
    
