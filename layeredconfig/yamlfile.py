import codecs

import yaml
from six import text_type as str

from . import DictSource

class YAMLFile(DictSource):
    def __init__(self, yamlfilename=None, writable=True, *args, **kwargs):
        super(YAMLFile, self).__init__(*args, **kwargs)
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        else:
            with codecs.open(yamlfilename) as fp:
                # do we need safe_load?
                self.source = yaml.safe_load(fp.read())
            self.yamlfilename = yamlfilename
            self.dirty = False
        self.writable = writable
        self.encoding = "utf-8"  # not sure this is ever really needed

    def get(self, key):
        ret = super(YAMLFile, self).get(key)
        if isinstance(ret, bytes):
            ret = ret.decode(self.encoding)
        return ret

    def save(self):
        assert not self.parent, "save() should only be called on root objects"
        if self.yamlfilename:
            with open(self.yamlfilename, "w") as fp:
                yaml.dump(self.source, fp, default_flow_style=False)
