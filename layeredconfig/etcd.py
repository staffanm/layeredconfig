import requests

from . import ConfigSource

# requires requests or python-etcd
class Etcd(ConfigSource):
    """Allows configuration to be read from (and stored in) an etcd store."""
    def __init__(self, url, writable=True, identifier="etcd"):
        super(Etcd, self).__init__()
        self.source = url
        self.writable = writable
        self.identifier = identifier
