Embedding configuration in python files
=======================================

In many cases, it's desirable to let the end user specify
configuration in the same langauge as the rest of the system (`Django
<https://www.djangoproject.com/>`_ and `Sphinx
<http://sphinx-doc.org/>`_ are examples of frameworks that works this
way). LayeredConfig provides the source :py:class:`~layeredconfig.PyFile`
that lets the user create configuration using normal python code.

If you create a file like ``conf.py`` with the following contents:

.. literalinclude:: examples/conf.py

.. note::

   The class ``Subsection`` will automatically be imported into
   ``conf.py`` and is used to create new subsections. Parameters in
   subsections are created as normal attributes on the subsection
   object.
		    
And load it, together with a :py:class:`~layeredconfig.Defaults`
source like in previous examples:

.. literalinclude:: examples/pyfile-example.py    
  :start-after: # begin example
  :end-before: # end example

The configuration object will act the same as in previous examples,
ie. values that are specified in ``conf.py`` be used, and values
specified in the Defaults object only used if ``conf.py`` doesn't
specify them.

.. note::

   The :py:class:`~layeredconfig.PyFile` source is read-only, so it
   should not be used when it's desirable to be able to save changed
   configuration parameters to a file. Use
   :py:class:`~layeredconfig.PyFile` or one of the other ``*File``
   sources in these cases.

It's also possible to keep system defaults in a separate python file,
load these with one :py:class:`~layeredconfig.PyFile` instance, and
then let the user override parts using a separate
:py:class:`~layeredconfig.PyFile` instance. Functionally, this is not
very different than loading system defaults using a
:py:class:`~layeredconfig.Defaults` source, but it might be preferable
in some cases. As an example, if the file ``defaults.py`` contains the
following code:

.. literalinclude:: examples/defaults.py

And a LayeredConfig object is initialized in the following way, then
the resulting configuration object works identically to the above:
		    
.. literalinclude:: examples/pyfile-example2.py
  :start-after: # begin example
  :end-before: # end example



