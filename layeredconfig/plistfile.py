from datetime import datetime
import plistlib
import sys

from six import text_type as str
from six import binary_type as bytes

from . import DictSource


class PListFile(DictSource):
    def __init__(self, plistfilename=None, writable=True, **kwargs):
        """Loads and optionally saves configuration files in PList
        format. Since PList has some support for typed values (supports
        numbers, lists, bools, datetimes *but not dates*), data from
        this source are sometimes typed, sometimes only available as
        strings.

        :param plistfile: The name of a PList file. Nested sections are 
                          turned into nested config objects.
        :type plistfile: str
        :param writable: Whether changes to the LayeredConfig object
                         that has this PListFile object amongst its
                         sources should be saved in the PList file.
        :type writable: bool
        """
        if sys.version_info >= (3,4):
            self.reader = plistlib.load
            self.writer = plistlib.dump
        else:
            self.reader = plistlib.readPlist
            self.writer = plistlib.writePlist
        super(PListFile, self).__init__(**kwargs)
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        else:
            with open(plistfilename, "rb") as fp:
                self.source = self.reader(fp)
            self.plistfilename = plistfilename
            self.dirty = False
        self.encoding = "utf-8"  # I hope this is a sensible default
        self.writable = writable
        
    def set(self, key, value):
        # plist natively supports some types but not all (notably not date)
        if not isinstance(value, (str, bool, int, list, datetime)):
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
            with open(self.plistfilename, "wb") as fp:
                self.writer(self.source, fp)
