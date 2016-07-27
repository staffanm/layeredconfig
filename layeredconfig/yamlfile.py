import codecs

import yaml

from . import DictSource

class YAMLFile(DictSource):
    def __init__(self, yamlfilename=None, writable=True, **kwargs):
        """Loads and optionally saves configuration files in YAML
        format. Since YAML (and the library implementing the support,
        PyYAML) has automatic support for typed values, data from this
        source are typed.

        :param yamlfile: The name of a YAML file. Nested
                         sections are turned into nested config objects.
        :type yamlfile: str
        :param writable: Whether changes to the LayeredConfig object
                         that has this YAMLFile object amongst its
                         sources should be saved in the YAML file.
        :type writable: bool

        """


        super(YAMLFile, self).__init__(**kwargs)
        if yamlfilename == None and 'parent' in kwargs and hasattr(kwargs['parent'], 'yamlfilename'):
            yamlfilename = kwargs['parent'].yamlfilename
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        elif kwargs.get('empty', False):
            self.source = {}
        else:
            with codecs.open(yamlfilename, encoding="utf-8") as fp:
                # do we need safe_load?
                self.source = yaml.safe_load(fp.read())
            self.yamlfilename = yamlfilename
            self.dirty = False
        self.writable = writable
        self.encoding = "utf-8"  # not sure this is ever really needed

    def get(self, key):
        ret = super(YAMLFile, self).get(key)
        # pyyaml by default makes strings whose content fit in ascii
        # available (on python2) as str objects, not unicode. Undo
        # this sillyness.
        if isinstance(ret, bytes):
            ret = ret.decode(self.encoding)
        # same with individual elements of lists
        elif isinstance(ret, list):
            for idx, val in enumerate(ret):
                if isinstance(ret[idx], bytes):
                    ret[idx] = ret[idx].decode(self.encoding)
        return ret

    def save(self):
        assert not self.parent, "save() should only be called on root objects"
        if self.yamlfilename:
            with codecs.open(self.yamlfilename, "w", encoding=self.encoding) as fp:
                yaml.safe_dump(self.source, fp, default_flow_style=False)
