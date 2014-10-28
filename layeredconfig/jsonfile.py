import json
from six import text_type as str

from . import DictSource

class JSONFile(DictSource):

    def __init__(self, jsonfilename=None, writable=True, *args, **kwargs):
        """

        :param jsonfile: A dict with configuration keys and values. If
                             any values are dicts, these are turned into
                             nested config objects.
        :type defaults: dict
        """
        super(JSONFile, self).__init__(*args, **kwargs)
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        else:
            with open(jsonfilename) as fp:
                self.source = json.load(fp)
            self.jsonfilename = jsonfilename
            self.dirty = False
        self.writable = writable

    def typed(self, key):
        # if the value is anything other than a string, we can be sure
        # that it contains useful type information.
        return not isinstance(self.get(key), str)

    def set(self, key, value):
        # simple stringification -- should perhaps only be done in the
        # save step through a method passed as a default parameter to
        # json dumps
        self.source[key] = str(value)

    def save(self):
        assert not self.parent, "save() should only be called on root objects"
        if self.jsonfilename:
            with open(self.jsonfilename, "w") as fp:
                json.dump(self.source, fp, indent=4)
