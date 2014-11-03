LayeredConfig compiles configuration from files, environment
variables, command line arguments, hard-coded default values, or other
backends, and makes it available to your code in a simple way.

.. literalinclude:: examples/firststep.py
  :start-after: # begin firststep
  :end-before: # end firststep

* A flexible system makes it possible to specify the sources of
  configuration information, including which source takes precedence
  (:ref:`precedence`). Implementations of common sources are included
  (:doc:`sources`) and an API for writing new ones exists
  (:doc:`configsource`)
  
* Configuration can include subsections
  (ie. ``config.downloading.refresh``, :ref:`subsection`) and if a
  subsection does not contain a requested setting, it can optionally
  be fetched from the main configuration (if ``config.module.retry``
  is missing, ``config.retry`` can be used instead, :ref:`cascading`).
* Configuration settings can be changed by your code (i.e. to update a
  "lastmodified" setting or similar), and changes can be persisted
  (saved) to the backend of your choice (:ref:`modification`)
* Configuration settings are typed (ie. if a setting should contain a
  date, it's made available to your code as a
  :py:class:`~datetime.date` object, not a :py:class:`str`). If
  settings are fetched from backends that do not themselves provide
  typed data (ie. environment variables, which by themselves are
  strings only), a system for type coercion makes it possible to
  specify how data should be converted (:ref:`typing`).

