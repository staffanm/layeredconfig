from . import DictSource

class Defaults(DictSource):
    def __init__(self, defaults, *args, **kwargs):
        """
        This source is initialized with a dict.

        :param defaults: A dict with configuration keys and values. If
                         any values are dicts, these are turned into
                         nested config objects.
        :type defaults: dict
        """
        super(Defaults, self).__init__(*args, **kwargs)
        self.source = defaults
