import json

from . import DictSource

class JSONFile(DictSource):

    def __init__(self, jsonfile, writable=True, identifier="defaults"):
        """

        :param jsonfile: A dict with configuration keys and values. If
                             any values are dicts, these are turned into
                             nested config objects.
        :type defaults: dict
        """
        super(JSONFile, self).__init__()
        with open(jsonfile) as fp:
            self.source = json.load(fp)
        self.jsonfile = jsonfile
        self.identifier = identifier
        self.writable = writable

    def typed(self, key):
        # if the value is anything other than a string, we can be sure
        # that it contains useful type information.
        return not isinstance(self.get(key), str)
