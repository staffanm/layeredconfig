Implementing custom ConfigSource classes
========================================

If you want to get configuration settings from some other sources than
the built-in sources, you should create a class that derives from
:py:class:`~layeredconfig.ConfigSource` and implement a few
methods.

If your chosen source can expose the settings as a (possibly nested)
:py:class:`dict`, it might be easier to derive from
:py:class:`~layeredconfig.DictSource` which already provide
implementations of many methods.

.. autoclass:: layeredconfig.ConfigSource
  :members:
  :undoc-members:
  :member-order: bysource


.. autoclass:: layeredconfig.DictSource
  :members:
  :member-order: bysource
