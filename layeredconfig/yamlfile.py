import yaml

from . import DictSource

class YAMLFile(DictSource):
    def __init__(self, yamlfile, writable=True, identifier="yaml"):
        super(YAMLFile, self).__init__()
        with open(yamlfile) as fp:
            # do we need safe_load? 
            self.source = yaml.safe_load(fp.read())
        self.writable = writable
        self.identifier = identifier
