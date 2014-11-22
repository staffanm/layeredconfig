.. :changelog:

History
=======

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
