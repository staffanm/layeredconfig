import six
from . import ConfigSource

try:
    import etcd
except ImportError:
    raise ImportError('python module for interacting with etcd not '
                      'installed, you should run "pip install '
                      'python-etcd" or similar')


class EtcdSource(ConfigSource):

    def __init__(self,
                 host='127.0.0.1',
                 port=4001,
                 read_timeout=60,
                 allow_redirect=True,
                 protocol='http',
                 cert=None,
                 ca_cert=None,
                 allow_reconnect=False,
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
            self.values = self.source.read(self.sectionkey)
        else:
            self.source = etcd.Client(host=host,
                                      port=port,
                                      read_timeout=read_timeout,
                                      allow_redirect=allow_redirect,
                                      protocol=protocol,
                                      cert=cert,
                                      ca_cert=ca_cert,
                                      allow_reconnect=allow_reconnect)
            self.sectionkey = "/"
            self.values = self.source.read(self.sectionkey)
        
    def has(self, key):
        for child in self.values.children:
            if not child.dir and self.sectionkey + key == child.key:
                return True
        return False

    def get(self, key):
        for child in self.values.children:
            if self.sectionkey + key == child.key:
                return child.value
        raise KeyError(key)
            
    def keys(self):
        for child in self.values.children:
            if not child.dir:
                yield child.key[len(self.sectionkey):]
            

    def typed(self, key):
        return False # in etcd, all keys seem to be strings. Or can
                     # they be ints, bools and lists (JSON supported
                     # types) maybe?

    def subsections(self):
        for child in self.values.children:
            if child.dir:
                yield child.key[len(self.sectionkey):]
        
    def subsection(self, key):
        prefix = self.sectionkey
        if not prefix.endswith("/"):
            prefix += "/"
        return EtcdSource(source=self.source, sectionkey=prefix+key+"/")
    
    def set(self, key=None, value=None):
        self.parent.set() # just set dirty flag
        if key and value:
            self.dirty[key] = value
        
    def save(self):
        for k in dirty:
            if isinstance(dirty[k], Etcd):
                dirty[k].save()
            else:
                self.source.write(k, dirty[k])
