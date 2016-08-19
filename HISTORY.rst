.. :changelog:

History
=======
0.3.1 (2016-08-20)
------------------

* Fixed bug #8 (layering a Commandline source over a YAMLFile with
  defined subsection resulted in crash in initialization. Thanks to
  @AnsonT for reporting this!
* The default URI used for EtcdStore was changed to reflect that port
  2379 should be used instead of 4001 (which was the default for etcd
  1.*).
* Support for Python 3.2 was dropped.

0.3.0 (2016-08-06)
------------------

* New staticmethod ``dump``, which returns the content of the passed
  config object as a dict. This is also used as a printable
  representation of a config object (through ``__repr__``).
* The intrinsic type of any typed setting may not be None any longer.
* If you subclass LayeredConfig, any created subsection will be
  instances of your subclass, not the base LayeredConfig class
* Layering multiple configuration files now works even when earlier
  files might lack subsections present in latter.

All of the above was done by @jedipi. Many thanks!

A number of unreported bugs, mostly concerning unicode handling and
type conversion in various sources, was also fixed.

0.2.2 (2016-01-24)
------------------

* Fixed a bug when using a class in a Default configuration for
  automatic coercion, where the type of the class isn't type (as is
  the case with the "newint" and other classes from the future
  module).

* Fixed a bug where loading configuration from multiple config files
  would crash if latter configs lacked subsections present in
  earlier. Thanks to @badkapitan!

0.2.1 (2014-11-26)
------------------

* Made the Commandline source interact better with "partially
  configured" ArgumentParser objects (parsers that has been configured
  with some, but not all, possible arguments).

0.2.0 (2014-11-22)
------------------

* Integration with argparse: The Commandline source now accepts an
  optional parse parameter, which should be a configured
  argparse.ArgumentParser object. Most features of argparse, such as
  specifying the type of arguments, and automatic help text
* A new source, PyFile, for reading configuration from python source
  files.
* Another new source, EtcdStore, for reading configuration from etcd
  stores.

0.1.0 (2014-11-03)
------------------

* First release on PyPI.
