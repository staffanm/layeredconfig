LayeredConfig compiles configuration from files, environment
variables, command line arguments, hard-coded default values, or other
backends, and makes it available to your code in a simple way::

    from layeredconfig import (LayeredConfig, Defaults, INIFile,
                               Environment, Commandline)
    
    # This represents four different way of specifying the value of the
    # configuration option "hello":
    
    # 1. hard-coded defaults
    defaults = {"hello": "is it me you're looking for?"}
    
    # 2. INI configuration file
    with open("myapp.ini", "w") as fp:
        fp.write("""
    [__root__]
    hello = kitty
    """)
    
    # 3. enironment variables
    import os
    os.environ['MYAPP_HELLO'] = 'goodbye'
    
    # 4.command-line arguments
    import sys
    sys.argv = ['./myapp.py', '--hello=world']
    
    # Create a config object that gets settings from these four
    # sources.
    config = LayeredConfig(Defaults(defaults),
                           INIFile("myapp.ini"),
                           Environment(prefix="MYAPP_"),
                           Commandline())
    
    # Prints "Hello world!", i.e the value provided by command-line
    # arguments. Latter sources take precedence over earlier sources.
    print("Hello %s!" % config.hello)

* A flexible system makes it possible to specify the sources of
  configuration information, including which source takes
  precedence. Implementations of many common sources are included and
  there is a API for writing new ones.
* Included configuration sources for INI files, YAML files, JSON file,
  PList files, etcd stores (read-write), Python source files,
  hard-coded defaults, command line options, environment variables
  (read-only).
* Configuration can include subsections
  (ie. ``config.downloading.refresh``) and if a
  subsection does not contain a requested setting, it can optionally
  be fetched from the main configuration (if ``config.module.retry``
  is missing, ``config.retry`` can be used instead).
* Configuration settings can be changed by your code (i.e. to update a
  "lastmodified" setting or similar), and changes can be persisted
  (saved) to the backend of your choice.
* Configuration settings are typed (ie. if a setting should contain a
  date, it's made available to your code as a
  ``datetime.date`` object, not a ``str``). If
  settings are fetched from backends that do not themselves provide
  typed data (ie. environment variables, which by themselves are
  strings only), a system for type coercion makes it possible to
  specify how data should be converted.

