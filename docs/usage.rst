Usage
=====

To use LayeredConfig in a project:

.. literalinclude:: examples/usage.py
  :start-after: # begin import-1
  :end-before: # end import-1

Also, import any Configuration sources you want to use. It's common to
have one source for code defaults, one configuration file (INI file in
this example), one using environment variables as source, and one
using command lines:
	      
.. literalinclude:: examples/usage.py
  :start-after: # begin import-2
  :end-before: # end import-2
		
Each configuration source must be initialized in some way. The
:py:class:`~layeredconfig.Default` source takes a dict, possibly
nested:

.. literalinclude:: examples/usage.py
  :start-after: # begin defaults
  :end-before: # end defaults

A configuration source such as :py:class:`~layeredconfig.INIFile`
takes the name of a file. In this example, we use a INI-style file.

.. literalinclude:: examples/usage.py
  :start-after: # begin inifile
  :end-before: # end inifile

.. note::

   LayeredConfig uses the :py:mod:`configparser` module, which
   requires that each setting is placed within a section. By default,
   settings placed within the ``[DEFAULT]`` section.

   In this example, we assume that there is a file called
   ``myapp.ini`` within the current directory with the following
   contents:

   .. literalinclude:: examples/myapp.ini

The :py:class:`~layeredconfig.Environment` uses environment variables
as the source of settings. Since the entire environment is not
suitable to use as a configuration, use of this source requires that a
``prefix`` is given. Only environment variables starting with this
prefix is used. Furthermore, since the name of environment variable
typically uses uppercase, they are by default lowercased by this
source. This means that, in this example, the value of the
environmentvariable ``MYAPP_HOME`` will be available as the
configuration setting ``home``.

.. literalinclude:: examples/usage.py
  :start-after: # begin environment
  :end-before: # end environment

Finally, the :py:class:`~layeredconfig.Commandline` processes the
contents of sys.argv and uses any parameter starting with ``--`` as a
setting, such as ``--home=/Users/staffan/Library/MyApp``. Arguments
that do not match this (such as positional arguments or short options
like ``-f``) are made available through the ``rest`` property, to be
used with eg. :py:mod:`argparse`.

.. literalinclude:: examples/usage.py
  :start-after: # begin commandline
  :end-before: # end commandline

Now that we have our config sources all set up, we can create the
actual configuration object:
	      
.. literalinclude:: examples/usage.py
  :start-after: # begin makeconfig
  :end-before: # end makeconfig

And we use the config object like this:
	      
.. literalinclude:: examples/usage.py
  :start-after: # begin useconfig
  :end-before: # end useconfig


Precedence
----------

A simple precedence system determines which setting is actually
used. In the above example, the printed string is "MyApp starting,
home in /opt/myapp". This is because while ``name`` was specified only
by the mydefaults source, ``home`` was specified by source with higher
predecence (``mycmdline``). The order of sources passed to
LayeredConfig determines predecence, with the last source having the
highest predecence.


Config sources
--------------

Apart from the sources used above, there are classes for settings
stored in JSON files, YAML files and PList files. Each source can to
varying extent be configured with different parameters. See :doc:`api`
for further details. 

You can also use a single source class multiple times, for example to have
one system-wide config file together with a user config file, where
settings in the latter override the former.

It's possible to write your own
:py:class:`~layeredconfig.ConfigSource`-based class to read (and
possibly write) from any concievable kind of source.

Typing
------

.. literalinclude:: examples/usage.py
  :start-after: # begin usetyping
  :end-before: # end usetyping

If a particular source doesn't contain intrinsic typing information,
other sources can be used to find out what type a particular setting
should be, and data is automatically converted.

.. note::

   string are always unicode strings (``str`` in python 3, ``unicode``
   in python 2). They are never byte sequences (``bytes`` in python 3,
   ``str`` in python 2)

Subsections
-----------

It's possible to divide up settings and group them in subsections. 

.. literalinclude:: examples/usage.py
  :start-after: # begin usesubconfig
  :end-before: # end usesubconfig

Cascading
---------

If a particular setting is not available in a subsection,
LayeredConfig can optionally look for the same setting in parent
sections.

.. literalinclude:: examples/usage.py
  :start-after: # begin usecascade
  :end-before: # end usecascade

Modification and persistance
----------------------------

It's possible to change a setting in a config object. It's also
possible to write out the changed settings to a config source
(ie. configuration files).


.. literalinclude:: examples/usage.py
  :start-after: # begin writeconfig
  :end-before: # end writeconfig

