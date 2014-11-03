from . import DictSource

class Defaults(DictSource):
    def __init__(self, defaults=None, **kwargs):
        """
        This source is initialized with a dict.

        :param defaults: A dict with configuration keys and values. If
                         any values are dicts, these are turned into
                         nested config objects.
        :type defaults: dict
        """
        super(Defaults, self).__init__(**kwargs)
        if defaults:
            self.source = defaults
            # if not, DictSource.__init__ ensures that self.source is
            # a empty dict
