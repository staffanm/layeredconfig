import yaml

from . import DictSource

class YAMLFile(DictSource):
    def __init__(self, yamlfile=None, writable=True, **kwargs):
        super(YAMLFile, self).__init__()
        if 'defaults' in kwargs:
            self.source = defaults
        else:
            with open(yamlfile) as fp:
                # do we need safe_load? 
                self.source = yaml.safe_load(fp.read())
            self.yamlfile = yamlfile
