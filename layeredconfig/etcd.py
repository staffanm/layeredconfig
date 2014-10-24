import requests

from . import ConfigSource

# requires requests or python-etcd
class Etcd(ConfigSource):
    """Allows configuration to be read from (and stored in) an etcd store."""
    def __init__(self, url, writable=True, *args, **kwargs):
        super(Etcd, self).__init__(*args, **kwargs)
        self.source = url
