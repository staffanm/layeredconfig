Usage
=====

To use LayeredConfig in a project::

    from layeredconfig import LayeredConfig, Defaults, Commandline, INIFile


Then read individual configuration settings using dot syntax::

    print(conf.home)
    if (conf.debug):
        print("Extra debugging info")
    
Config sources
--------------

There are a number of sources available, see :doc:`api`.

Typing
------

If a particular source doesn't contain intrinsic typing information,
other sources can be used to find out what type a particular setting
should be, and data is automatically converted.

Precedence
----------

A simple precedence system determines which setting is actually 

Subsections
-----------

It's possible to divide up settings and group them in subsections. 

Cascading
---------

If a particular setting is not available in a subsection,
LayeredConfig can optionally look for the same setting in parent
sections.

Modification and persistance
----------------------------

It's possible to change a setting in a config object. It's also
possible to write out the changed settings to a config source
(ie. configuration files).



