#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
test_layeredconfig
----------------------------------

Tests for `layeredconfig` module.
"""

import os
import logging
import unittest
from six import text_type as str
from datetime import date, datetime

# The system under test
from layeredconfig import LayeredConfig, Defaults, INIFile, JSONFile, Environment, Commandline


class TestHelper(object):
    # First, a number of straightforward tests for any
    # ConfigSource-derived object. Concrete test classes should set up
    # self.simple and self.complex instances to match these.
    def test_keys(self):
        self.assertEqual(set(self.simple.keys()),
                         set(('home', 'processes', 'force',
                              'extra', 'expires', 'lastrun')))
        self.assertEqual(set(self.complex.keys()),
                         set(('home', 'processes', 'force', 'extra')))

    def test_subsection_keys(self):
        self.assertEqual(set(self.complex.subsection('mymodule').keys()),
                         set(('force', 'extra', 'expires')))

    def test_subsections(self):
        self.assertEqual(set(self.simple.subsections()),
                         set())
        self.assertEqual(set(self.complex.subsections()),
                         set(('mymodule', 'extramodule')))

    def test_subsection_nested(self):
        subsec = self.complex.subsection('mymodule')
        self.assertEqual(set(subsec.subsections()),
                         set(('arbitrary',)))
        
    def test_has(self):
        for key in self.simple.keys():
            self.assertTrue(self.simple.has(key))

    def test_typed(self):
        for key in self.simple.keys():
            self.assertTrue(self.simple.typed(key))
                
    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), 4)
        self.assertEqual(self.simple.get("force"), True)
        self.assertEqual(self.simple.get("extra"), ['foo', 'bar'])
        self.assertEqual(self.simple.get("expires"), date(2014, 10, 15))
        self.assertEqual(self.simple.get("lastrun"),
                         datetime(2014, 10, 15, 14, 32, 7))

    # Then, two validation helpers for checking a complete
    # LayeredConfig object, where validation can be performed
    # different depending on the abilities of the source (eg. typing)
    def _test_mainsection(self, cfg,
                          int_type=int,
                          bool_type=bool,
                          list_type=list,
                          date_type=date,
                          datetime_type=datetime):

        self.assertIs(type(cfg.home), str)
        self.assertEqual(cfg.home, 'mydata')
        self.assertIs(type(cfg.processes), int_type)
        self.assertEqual(cfg.processes, int_type(4))
        self.assertIs(type(cfg.force), bool_type)
        self.assertEqual(cfg.force, bool_type(True))
        self.assertIs(type(cfg.extra), list_type)
        if list_type == str:
            want = "foo, bar"  # recommended serialization of lists of strings
        else:
            want = ['foo', 'bar']
        self.assertEqual(cfg.extra, want)
        self.assertIs(type(cfg.expires), date_type)
        if date_type == str:
            self.assertEqual(cfg.expires, date_type(date(2014, 10, 15)))
        else:
            self.assertEqual(cfg.expires, date(2014, 10, 15))
        self.assertIs(type(cfg.lastrun), datetime_type)
        if datetime_type == str:
            self.assertEqual(cfg.lastrun,
                             datetime_type(datetime(2014, 10, 15, 14, 32, 7)))
        else:
            self.assertEqual(cfg.lastrun, datetime(2014, 10, 15, 14, 32, 7))

    def _test_subsections(self, cfg,
                          int_type=int,
                          bool_type=bool,
                          list_type=list,
                          date_type=date,
                          datetime_type=datetime,
                          arbitrary_nesting=True):
        self.assertEqual(cfg.home, 'mydata')
        with self.assertRaises(AttributeError):
            cfg.mymodule.home
        self.assertEqual(cfg.processes, int_type(4))
        with self.assertRaises(AttributeError):
            cfg.mymodule.processes
        self.assertEqual(cfg.force, bool_type(True))
        self.assertEqual(cfg.mymodule.force, bool_type(False))
        if list_type == str:
            want = "foo, bar"  # recommended serialization of lists of strings
        else:
            want = ['foo', 'bar']
        self.assertEqual(cfg.extra, want)
        if list_type == str:
            want = "foo, baz"
        else:
            want = ['foo', 'baz']
        self.assertEqual(cfg.mymodule.extra, want)
        # not supported for INIFile
        if arbitrary_nesting:
            self.assertEqual(cfg.mymodule.arbitrary.nesting.depth, 'works')
        with self.assertRaises(AttributeError):
            cfg.expires
        if date_type == str:
            self.assertEqual(cfg.mymodule.expires,
                             date_type(date(2014, 10, 15)))
        else:
            self.assertEqual(cfg.mymodule.expires, date(2014, 10, 15))

# common helper
class TestINIFileHelper(TestHelper):

    def setUp(self):
        with open("simple.ini", "w") as fp:
            fp.write("""
[__root__]
home = mydata
processes = 4
force = True
extra = foo, bar
expires = 2014-10-15
lastrun = 2014-10-15 14:32:07
""")

        with open("complex.ini", "w") as fp:
            fp.write("""
[__root__]
home = mydata
processes = 4
force = True
extra = foo, bar

[mymodule]
force=False
extra = foo, baz
expires = 2014-10-15

[extramodule]
unique = True
""")

    def tearDown(self):
        os.unlink("simple.ini")
        os.unlink("complex.ini")


class TestDefaults(unittest.TestCase, TestHelper):

    simple = Defaults({'home': 'mydata',
                       'processes': 4,
                       'force': True,
                       'extra': ['foo', 'bar'],
                       'expires': date(2014, 10, 15),
                       'lastrun': datetime(2014, 10, 15, 14, 32, 7)})

    complex = Defaults({'home': 'mydata',
                        'processes': 4,
                        'force': True,
                        'extra': ['foo', 'bar'],
                        'mymodule': {'force': False,
                                     'extra': ['foo', 'baz'],
                                     'expires': date(2014, 10, 15),
                                     'arbitrary': {
                                         'nesting': {
                                             'depth': 'works'
                                         }
                                     }
                                 },
                        'extramodule': {'unique': True}})

    def test_config(self):
        cfg = LayeredConfig(self.simple)
        self._test_mainsection(cfg)

    def test_config_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_subsections(cfg)


class TestINIFile(TestINIFileHelper, unittest.TestCase):

    def setUp(self):
        super(TestINIFile, self).setUp()
        self.simple = INIFile("simple.ini")
        self.complex = INIFile("complex.ini")


    # Overrides of TestHelper.test_get, .test_typed and
    # .test_subsection_nested due to limitations of INIFile
    # INIFile carries no typing information
    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), "4")
        self.assertEqual(self.simple.get("force"), "True")
        self.assertEqual(self.simple.get("extra"), "foo, bar")
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"), "2014-10-15 14:32:07")

    def test_typed(self):
        for key in self.simple.keys():
            self.assertFalse(self.simple.typed(key))

    # INIFile doesn't support nested subsections
    def test_subsection_nested(self):
        subsec = self.complex.subsection('mymodule')
        self.assertEqual(set(subsec.subsections()),
                         set(()))

    def test_inifile(self):
        cfg = LayeredConfig(self.simple)
        self._test_mainsection(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str)

    def test_inifile_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_subsections(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str,
                               arbitrary_nesting=False)

    def test_inifile_nonexistent(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        cfg = LayeredConfig(INIFile("nonexistent.ini"))
        self.assertEqual([], list(cfg))

        
class TestJSONFile(unittest.TestCase, TestHelper):

    def setUp(self):
        with open("simple.json", "w") as fp:
            fp.write("""
{"home": "mydata",
 "processes": 4,
 "force": true,
 "extra": ["foo", "bar"],
 "expires": "2014-10-15",
 "lastrun": "2014-10-15 14:32:07"}
""")

        with open("complex.json", "w") as fp:
            fp.write("""
{"home": "mydata",
 "processes": 4,
 "force": true,
 "extra": ["foo", "bar"],
 "mymodule": {"force": false,
              "extra": ["foo", "baz"],
              "expires": "2014-10-15",
              "arbitrary": {
                  "nesting": {
                      "depth": "works"
                  }
              }
          },
 "extramodule": {"unique": true}
}
""")
        self.simple = JSONFile("simple.json")
        self.complex = JSONFile("complex.json")

    def tearDown(self):
        os.unlink("simple.json")
        os.unlink("complex.json")

    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), 4)
        self.assertEqual(self.simple.get("force"), True)
        self.assertEqual(self.simple.get("extra"), ['foo', 'bar'])
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"), "2014-10-15 14:32:07")

    def test_typed(self):
        for key in self.simple.keys():
            # JSON can type ints, bools and lists
            if key in ("processes", "force", "extra"):
                self.assertTrue(self.simple.typed(key))
            else:
                self.assertFalse(self.simple.typed(key))                
        
    def test_jsonfile(self):
        cfg = LayeredConfig(self.simple)
        self._test_mainsection(cfg,
                               int_type=int,
                               bool_type=bool,
                               list_type=list,
                               date_type=str,
                               datetime_type=str)

    def test_jsonfile_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_subsections(cfg,
                               int_type=int,
                               bool_type=bool,
                               list_type=list,
                               date_type=str,
                               datetime_type=str,
                               arbitrary_nesting=True)

class TestCommandline(unittest.TestCase, TestHelper):

    simple = Commandline(['--home=mydata',
                          '--processes=4',
                          '--force',  # note implicit boolean typing
                          '--extra=foo',
                          '--extra=bar',
                          '--expires=2014-10-15',
                          '--lastrun=2014-10-15 14:32:07'])

    complex = Commandline(['--home=mydata',
                           '--processes=4',
                           '--force=True',
                           '--extra=foo',
                           '--extra=bar',
                           '--mymodule-force=False',
                           '--mymodule-extra=foo',
                           '--mymodule-extra=baz',
                           '--mymodule-expires=2014-10-15',
                           '--mymodule-arbitrary-nesting-depth=works',
                           '--extramodule-unique'])

    # Overrides of TestHelper.test_get, .test_typed and and due to
    # limitations of Commandline (carries almost no typeinfo)
    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), "4")
        self.assertEqual(self.simple.get("force"), True)
        self.assertEqual(self.simple.get("extra"), ['foo','bar']) # note typed!
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"), "2014-10-15 14:32:07")

    def test_typed(self):
        for key in self.simple.keys():
            # these should be typed as bool and list, respectively
            if key in ("force", "extra"):
                self.assertTrue(self.simple.typed(key))
            else:
                self.assertFalse(self.simple.typed(key))                

    def test_commandline(self):
        cfg = LayeredConfig(self.simple)
        self._test_mainsection(cfg,
                               int_type=str,
                               date_type=str,
                               datetime_type=str, 
                               bool_type=bool,  # not always, see below
                               list_type=list)

    def test_commandline_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_subsections(cfg,
                               int_type=str,
                               bool_type=str,  # "--mymodule-force=False"
                               list_type=list,
                               date_type=str,
                               datetime_type=str)


class TestEnvironment(unittest.TestCase, TestHelper):

    simple = Environment({'MYAPP_HOME': 'mydata',
                          'MYAPP_PROCESSES': '4',
                          'MYAPP_FORCE': 'True',
                          'MYAPP_EXTRA': 'foo, bar',
                          'MYAPP_EXPIRES': '2014-10-15',
                          'MYAPP_LASTRUN': '2014-10-15 14:32:07'},
                         prefix="MYAPP_")
    complex = Environment({'MYAPP_HOME': 'mydata',
                           'MYAPP_PROCESSES': '4',
                           'MYAPP_FORCE': 'True',
                           'MYAPP_EXTRA': 'foo, bar',
                           'MYAPP_MYMODULE_FORCE': 'False',
                           'MYAPP_MYMODULE_EXTRA': 'foo, baz',
                           'MYAPP_MYMODULE_EXPIRES': '2014-10-15',
                           'MYAPP_MYMODULE_ARBITRARY_NESTING_DEPTH': 'works',
                           'MYAPP_EXTRAMODULE_UNIQUE': 'True'},
                          prefix="MYAPP_")

    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), "4")
        self.assertEqual(self.simple.get("force"), "True")
        self.assertEqual(self.simple.get("extra"), "foo, bar")
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"), "2014-10-15 14:32:07")

    def test_typed(self):
        for key in self.simple.keys():
            self.assertFalse(self.simple.typed(key))

    def test_environment(self):
        cfg = LayeredConfig(self.simple)
        self._test_mainsection(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str)

    def test_environment_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_subsections(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str)

class TestTyping(unittest.TestCase, TestHelper):
    types = {'home': str,
             'processes': int,
             'force': bool,
             'extra': list,
             'expires': date,
             'lastrun': datetime,
             'mymodule': {'force': bool,
                          'extra': list,
                          'expires': date,
                          'lastrun': datetime,
                      }
             }
    
    def test_typed_commandline(self):
        cmdline = ['--home=mydata',
                   '--processes=4',
                   '--force=True',  # results in string, not bool
                   '--extra=foo',
                   '--extra=bar',
                   # '--expires=2014-10-15',
                   # '--lastrun=2014-10-15 14:32:07',
                   '--implicitboolean',
                   '--mymodule-force=False',
                   '--mymodule-extra=foo',
                   '--mymodule-extra=baz',
                   '--mymodule-expires=2014-10-15',
                   '--mymodule-arbitrary-nesting-depth=works']
        cfg = LayeredConfig(Defaults(self.types), Commandline(cmdline))
        self._test_subsections(cfg)
        self.assertTrue(cfg.implicitboolean)
        self.assertIs(type(cfg.implicitboolean), bool)

    def test_typed_override(self):
        # make sure this auto-typing isn't run for bools
        types = {'logfile': True}
        cmdline = ["--logfile=out.log"]
        cfg = LayeredConfig(Defaults(types), Commandline(cmdline))
        self.assertEqual(cfg.logfile, "out.log")

    def test_typed_commandline_cascade(self):
        # the test here is that _load_commandline must use _type_value property.
        defaults = {'force':True,
                    'lastdownload':datetime,
                    'mymodule': {}}
        cmdline = ['--mymodule-force=False']
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline), cascade=True)
        subconfig = getattr(cfg, 'mymodule')
        self.assertIs(type(subconfig.force), bool)
        self.assertEqual(subconfig.force, False)
        # test typed config values that have no actual value
        
        self.assertEqual(cfg.lastdownload, None)
        self.assertEqual(subconfig.lastdownload, None)


class TestTypingINIFile(TestINIFileHelper, TestTyping):
    
    def test_typed_inifile(self):
        # FIXME: create inifile
        cfg = LayeredConfig(Defaults(self.types), INIFile("ferenda.ini"))
        self._test_subsections(cfg)


class TestLayered(unittest.TestCase):
    def test_layered(self):
        defaults = {'loglevel':'ERROR'}
        cmdline = ['--loglevel=DEBUG']
        cfg = LayeredConfig(Defaults(defaults))
        self.assertEqual(cfg.loglevel, 'ERROR')
        cfg = LayeredConfig(Defaults(defaults), INIFile("ferenda.ini"))
        self.assertEqual(cfg.loglevel, 'INFO')
        cfg = LayeredConfig(Defaults(defaults), INIFile("ferenda.ini"), Commandline(cmdline))
        self.assertEqual(cfg.loglevel, 'DEBUG')
        self.assertEqual(['loglevel', 'home', 'processes', 'force', 'extra'], list(cfg))



    def test_layered_subsections(self):
        defaults = OrderedDict((('force',False),
                                ('home','thisdata'),
                                ('loglevel','INFO')))
        cmdline=['--mymodule-home=thatdata','--mymodule-force'] # 
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline), cascade=True)
        self.assertEqual(cfg.mymodule.force, True)
        self.assertEqual(cfg.mymodule.home, 'thatdata')
        self.assertEqual(cfg.mymodule.loglevel, 'INFO')

        defaults = {'mymodule':defaults}
        cmdline=['--home=thatdata','--force'] # 
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline), cascade=True)
        self.assertEqual(cfg.mymodule.force, True)
        self.assertEqual(cfg.mymodule.home, 'thatdata')
        self.assertEqual(cfg.mymodule.loglevel, 'INFO')


        self.assertEqual(['force', 'home', 'loglevel'], list(cfg.mymodule))


class TestModifications(unittest.TestCase):
    def test_modified(self):
        defaults = {'lastdownload':None}
        cfg = LayeredConfig(Defaults(defaults))
        now = datetime.now()
        cfg.lastdownload = now
        self.assertEqual(cfg.lastdownload,now)
        

    def test_modified_subsections(self):
        defaults = {'force':False,
                    'home':'thisdata',
                    'loglevel':'INFO'}
        cmdline=['--mymodule-home=thatdata','--mymodule-force'] # 
        cfg = LayeredConfig(Defaults(defaults), INIFile("ferenda.ini"), Commandline(cmdline), cascade=True)
        cfg.mymodule.loglevel = 'ERROR'

    def test_write_configfile(self):
        cfg = LayeredConfig(INIFile("ferenda.ini"))
        cfg.mymodule.lastrun = datetime(2013,9,18,15,41,0)
        # calling write for any submodule will force a write of the
        # entire config file
        LayeredConfig.write(cfg.mymodule)
        want = """[__root__]
home = mydata
processes = 4
loglevel = INFO
force = True
extra = ['foo','bar']

[mymodule]
loglevel = DEBUG
force = False
        extra = ['foo','baz']
lastrun = 2013-09-18 15:41:00

"""
        got = util.readfile("ferenda.ini").replace("\r\n","\n")
        #if not isinstance(got, six.text_type):
        #    got = got.decode("utf-8")
        self.assertEqual(want,got)

    def test_write_noconfigfile(self):
        cfg = LayeredConfig(Defaults({'lastrun': datetime(2012,9,18,15,41,0)}))
        cfg.lastrun = datetime(2013,9,18,15,41,0)
        LayeredConfig.write(cfg)


class TestAccessors(unittest.TestCase):

    def test_set(self):
        # a value is set in a particular underlying source, and the
        # dirty flag isn't set.
        cfg = LayeredConfig(INIFile("simple.ini"))
        LayeredConfig.set(cfg, 'lastrun', datetime(2013, 9, 18, 15, 41, 0),
                          "defaults")
        self.assertEqual(datetime(2013, 9, 18, 15, 41, 0), cfg.lastrun)
        self.assertFalse(cfg._inifile_dirty)

    def test_get(self):
        cfg = LayeredConfig(Defaults({'codedefaults': 'yes',
                                      'force': False,
                                      'home': '/usr/home'}),
                            INIFile('simple.ini'))
        # and then do a bunch of get()

if __name__ == '__main__':
    unittest.main()
