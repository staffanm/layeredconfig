import six
from . import ConfigSource

import requests

class EtcdSource(ConfigSource):

    def __init__(self, baseurl="http://127.0.0.1:4001/v2/",
                 **kwargs):
        """Loads configuration from a `etcd store
        <https://github.com/coreos/etcd>`_.

        Parameters have the same meaning and default values as
        :py:class:`etcd.Client`.

        ``etcd`` has no concept of typed values, so all data from this
        source are returned as strings.
        """
        if kwargs.get('source'):
            # subsection
            self.source = kwargs['source']
            self.sectionkey = kwargs['sectionkey']
        else:
            self.source = baseurl + "keys"
            self.sectionkey = "/"
        resp = requests.get(self.source + self.sectionkey)
        self.values = resp.json()['node']['nodes']
        
    def has(self, key):
        for child in self.values:
            if 'dir' not in child and self.sectionkey + key == child['key']:
                return True
        return False

    def get(self, key):
        for child in self.values:
            if self.sectionkey + key == child['key']:
                return child['value']
        raise KeyError(key)
            
    def keys(self):
        for child in self.values:
            if 'dir' not in child:
                yield child['key'][len(self.sectionkey):]
            
    def typed(self, key):
        return False # in etcd, all keys seem to be strings. Or can
                     # they be ints, bools and lists (JSON supported
                     # types) maybe?

    def subsections(self):
        for child in self.values:
            if 'dir' in child:
                yield child['key'][len(self.sectionkey):]
        
    def subsection(self, key):
        prefix = self.sectionkey
        if not prefix.endswith("/"):
            prefix += "/"
        return EtcdSource(source=self.source, sectionkey=prefix+key+"/")
    
    def set(self, key=None, value=None):
        self.dirty = True
        if self.parent:
            self.parent.set()
        if not self.dirtyvalues:
            self.dirtyvalues = []
        if key and value:
            self.dirtyvalues[key] = value
        
    def save(self):
        for k in self.dirtyvalues:
            self.source.write(k, dirty[k])
