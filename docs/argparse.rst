Using LayeredConfig with ``argparse``
=====================================

The standard module for handling command line arguments in python is
:py:mod:`argparse`. This module handles much of the same things as
LayeredConfig does (eg. defining the default values and types of
arguments and making them easily accessed), but it isn't able to read
parameter values from other sources such as INI files or environment
variables.

LayeredConfig integrates with argparse through the
:py:class:`~layeredconfig.Commandline` config source. If you have
existing code to set up an :py:class:`argparse.ArgumentParser` object,
you can re-use that with LayeredConfig.

.. literalinclude:: examples/argparse-example.py
  :start-after: # begin import
  :end-before: # end import

After this setup, you might want to create any number of config
sources. In this example we use a :py:class:`~layeredconfig.Defaults`
object, mostly used for specifying the type of different arguments.

.. literalinclude:: examples/argparse-example.py
  :start-after: # begin defaults
  :end-before: # end defaults

And also an :py:class:`~layeredconfig.INIFile` that is used to store
actual values for most parameters.
	       
.. literalinclude:: examples/argparse-example.py
  :start-after: # begin inifile
  :end-before: # end inifile

Next up, we create an instance of :py:class:`argparse.ArgumentParser`
in the normal way. Note that in this example, we specify the types of
some of the parameters, since this is representative of how
ArgumentParser normally is used. But you can also omit this
information (the ``action`` and ``type`` parameters to
:py:meth:`~argparse.ArgumentParser.add_argument`) as long as you
provide information through a Defaults config source object.

Note: we don't add arguments for ``--duedate`` or ``--submodule-lastrun`` to
show that LayeredConfig can define these arguments based on other
sources. Also note that defaults values are automatically fetched from
either defaults or inifile.

.. literalinclude:: examples/argparse-example.py
  :start-after: # begin argparse
  :end-before: # end argparse

Now, instead of calling
:py:meth:`~argparse.ArgumentParser.parse_args`, you can pass this
initialized parser object as a named parameter when creating a
:py:class:`~layeredconfig.Commandline` source, and use this to create
a :py:class:`~layeredconfig.LayeredConfig` object.

Note that you can use short parameters if you want, as long as you
define long parameters (that map to your other parameter names) as
well

.. literalinclude:: examples/argparse-example.py
  :start-after: # begin layeredconfig
  :end-before: # end layeredconfig

The standard feature of argparse to create a help text if the ``-h``
parameter is given still exists. Note that it will also display
parameters such as `--name``, which was defined in the
:py:class:`~layeredconfig.Defaults` object, not in the parser object.

.. literalinclude:: examples/argparse-example.py
  :start-after: # begin showhelp
  :end-before: # end showhelp


	       
