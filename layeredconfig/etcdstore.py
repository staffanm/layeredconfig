import six
from . import ConfigSource

import requests

class EtcdStore(ConfigSource):

    def __init__(self, baseurl="http://127.0.0.1:4001/v2/",
                 **kwargs):
        """Loads configuration from a `etcd store
        <https://github.com/coreos/etcd>`_.

        :param baseurl: The main endpoint of the etcd store

        ``etcd`` has no concept of typed values, so all data from this
        source are returned as strings.
        """
        super(EtcdStore, self).__init__(**kwargs)
        if kwargs.get('source'):
            # subsection
            self.source = kwargs['source']
            self.sectionkey = kwargs['sectionkey']
        else:
            self.source = baseurl + "keys"
            self.sectionkey = "/"
        resp = requests.get(self.source + self.sectionkey)
        self.values = resp.json()['node']['nodes']
        self.dirtyvalues = {}
        self.writable = kwargs.get("writable", True)
        self.subsectioncache = {}

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
        if key not in self.subsectioncache:
            prefix = self.sectionkey
            if not prefix.endswith("/"):
                prefix += "/"
            self.subsectioncache[key] = EtcdStore(source=self.source,
                                                  parent=self,
                                                  sectionkey=prefix+key+"/")
        return self.subsectioncache[key]

    def set(self, key=None, value=None):
        self.dirty = True
        if self.parent:
            self.parent.set()
        if key and value:
            self.dirtyvalues[key] = value

    def _strvalue(self, value):
        if isinstance(value, bool):
            return str(value).lower()
        else:
            return super(EtcdStore, self)._strvalue(value)

    def save(self):
        for k in self.dirtyvalues:
            requests.put(self.source+self.sectionkey+k,
                         data={'value': self._strvalue(self.dirtyvalues[k])})
        self.dirtyvalues = {}
        for subsection in self.subsections():
            self.subsection(subsection).save()
        self.dirty = False
