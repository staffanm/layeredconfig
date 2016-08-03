import json
from six import text_type as str

from . import DictSource


class JSONFile(DictSource):

    def __init__(self, jsonfilename=None, writable=True, **kwargs):
        """Loads and optionally saves configuration files in JSON
        format. Since JSON has some support for typed values (supports
        numbers, lists, bools, but not dates or datetimes), data from
        this source are sometimes typed, sometimes only available as
        strings.

        :param jsonfile: The name of a JSON file, whose root element
                         should be a JSON object (python dict). Nested
                         objects are turned into nested config objects.
        :type jsonfile: str
        :param writable: Whether changes to the LayeredConfig object
                         that has this JSONFile object amongst its
                         sources should be saved in the JSON file.
        :type writable: bool

        """
        super(JSONFile, self).__init__(**kwargs)
        if jsonfilename == None and 'parent' in kwargs and hasattr(kwargs['parent'], 'jsonfilename'):
            jsonfilename = kwargs['parent'].jsonfilename
        if 'defaults' in kwargs:
            self.source = kwargs['defaults']
        elif kwargs.get('empty', False):
            self.source = {}
        else:
            with open(jsonfilename) as fp:
                self.source = json.load(fp)
            self.jsonfilename = jsonfilename
            self.dirty = False
        self.writable = writable

    def typed(self, key):
        # if the value is anything other than a string, we can be sure
        # that it contains useful type information.
        
        return self.has(key) and not isinstance(self.get(key), str)

    def set(self, key, value):
        # simple stringification -- should perhaps only be done in the
        # save step through a method passed as a default parameter to
        # json dumps
        self.source[key] = str(value)

    def save(self):
        assert not self.parent, "save() should only be called on root objects"
        if self.jsonfilename:
            with open(self.jsonfilename, "w") as fp:
                json.dump(self.source, fp, indent=4, separators=(',',': '), sort_keys=True)
