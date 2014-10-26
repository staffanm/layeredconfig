
.. image:: https://badge.fury.io/py/layeredconfig.png
    :target: http://badge.fury.io/py/layeredconfig

.. image:: https://travis-ci.org/staffanm/layeredconfig.png?branch=master
        :target: https://travis-ci.org/staffanm/layeredconfig

.. image:: https://ci.appveyor.com/api/projects/status/nnfqv9jhxh3afgn0/branch/master
    :target: https://ci.appveyor.com/project/staffanm/layeredconfig/branch/master

.. image:: https://coveralls.io/repos/staffanm/layeredconfig/badge.png?branch=master
    :target: https://coveralls.io/r/staffanm/layeredconfig

.. image:: https://landscape.io/github/staffanm/layeredconfig/master/landscape.png
   :target: https://landscape.io/github/staffanm/layeredconfig/master
   :alt: Code Health

.. image:: https://pypip.in/d/layeredconfig/badge.png
        :target: https://pypi.python.org/pypi/layeredconfig

LayeredConfig compiles configuration from files, environment
variables, command line arguments, hard-coded default values, `etcd
stores <https://coreos.com/docs/#distributed-configuration>`_ or other
backends, and makes it available to your code in a simple way.


.. literalinclude:: examples/firststep.py
  :start-after: # begin firststep

A flexible system makes it possible to specify the sources of
configuration information including which source takes precedence. It
support INI-style files, JSON files, YAML files and PList files.

Configuration can include subsections
(ie. ``config.downloading.refresh``) and if a subsection does not
contain a requested setting, it can optionally be fetched from
the main configuration (if ``config.module.retry`` is missing,
``config.retry`` can be used instead).

Configuration can be changed programatically (i.e. to update a
"lastmodified" setting or similar), and changes can be saved to
the backend of your choice.

Configuration settings are typed (ie. if a setting should contain a
date, it's made available to your code as a :py:class:`~datetime.date`
object, not a :py:class:`str`). If settings are fetched from backends
that do not themselves provide typed data (ie. environment variables,
which by themselves are strings only), a system for type coercion
makes it possible to specify how data should be converted.

* Free software: BSD license
* Documentation: https://layeredconfig.readthedocs.org.
