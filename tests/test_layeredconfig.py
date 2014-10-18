#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
test_layeredconfig
----------------------------------

Tests for `layeredconfig` module.
"""

import os
import unittest
from six import text_type as str
from datetime import date, datetime

# The system under test
from layeredconfig import LayeredConfig, Defaults, INIFile, Environment, Commandline


class TestHelper(object):
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
            want = "['foo','bar']"
        else:
            want = ['foo', 'bar']
        self.assertEqual(cfg.extra, want)
        self.assertIs(type(cfg.expires), date_type)
        self.assertEqual(cfg.expires, date_type(date(2014, 10, 15)))
        self.assertIs(type(cfg.lastrun), datetime_type)
        self.assertEqual(cfg.lastrun, datetime_type(datetime(2014, 10, 15, 14, 32, 7)))

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
            want = "['foo','bar']"
        else:
            want = ['foo', 'bar']
        self.assertEqual(cfg.extra, want)
        if list_type == str:
            want = "['foo','baz']"
        else:
            want = ['foo', 'baz']
        self.assertEqual(cfg.mymodule.extra, want)
        # not supported for INIFile
        if arbitrary_nesting:
            self.assertEqual(cfg.mymodule.arbitrary.nesting.depth, 'works')
        with self.assertRaises(AttributeError):
            cfg.expires
        self.assertEqual(cfg.mymodule.expires,
                         date_type(date(2014, 10, 15)))


class TestINIFileHelper(TestHelper):

    def setUp(self):
        with open("ferenda.ini", "w") as fp:
            fp.write("""
[__root__]
home = mydata
processes = 4
force = True
extra = ['foo','bar']
expires = 2014-10-15
lastrun = 2014-10-15 14:32:07
""")

    def tearDown(self):
        os.unlink("ferenda.ini")

class TestDefaults(unittest.TestCase, TestHelper):

    def test_defaults(self):
        cfg = LayeredConfig(
            Defaults({'home': 'mydata',
                      'processes': 4,
                      'force': True,
                      'extra': ['foo', 'bar'],
                      'expires': date(2014, 10, 15),
                      'lastrun': datetime(2014, 10, 15, 14, 32, 7)}))
        self._test_mainsection(cfg)

    def test_defaults_subsections(self):
        cfg = LayeredConfig(
            Defaults({'home': 'mydata',
                      'processes': 4,
                      'force': True,
                      'extra': ['foo', 'bar'],
                      'mymodule': {'force': False,
                                   'extra': ['foo', 'baz'],
                                   'expires': datetime(2014, 10, 15),
                                   'arbitrary': {
                                       'nesting': {
                                           'depth': 'works'
                                       }
                                   }
                               }}))
        self._test_subsections(cfg)


class TestINIFile(TestINIFileHelper, unittest.TestCase):
    def test_inifile(self):
        cfg = LayeredConfig(INIFile("ferenda.ini"))
        self._test_mainsection(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str)

    def test_inifile_subsections(self):
        with open("ferenda.ini", "w") as fp:
            fp.write("""
[__root__]
home = mydata
processes = 4
loglevel = INFO
force = True
extra = ['foo','bar']

[mymodule]
loglevel = DEBUG
force=False
extra = ['foo','baz']
expires: 2014-10-15
lastrun = 2014-10-15 14:32:07
""")
        cfg = LayeredConfig(INIFile("ferenda.ini"))
        self._test_subsections(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=str,
                               date_type=str,
                               datetime_type=str,
                               arbitrary_nesting=False)

    def test_inifile_nonexistent(self):
        cfg = LayeredConfig(INIFile("nonexistent.ini"))
        self.assertEqual([], list(cfg))


class TestCommandline(unittest.TestCase, TestHelper):

    def test_commandline(self):
        cmdline = ['--home=mydata',
                   '--processes=4',
                   '--loglevel=INFO',
                   '--force=True',  # results in string, not bool
                   '--extra=foo',
                   '--extra=bar',
                   '--implicitboolean']
        cfg = LayeredConfig(Commandline(cmdline))
        self._test_mainsection(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=list,
                               date_type=str,
                               datetime_type=str)

        # extra test of implicitboolean
        self.assertTrue(cfg.implicitboolean)
        self.assertIs(type(cfg.implicitboolean), bool)
        
    def test_commandline_subsections(self):
        cmdline = ['--home=mydata',
                   '--processes=4',
                   '--loglevel=INFO',
                   '--force=True',
                   '--extra=foo',
                   '--extra=bar',
                   '--mymodule-loglevel=DEBUG',
                   '--mymodule-force=False',
                   '--mymodule-extra=foo',
                   '--mymodule-extra=baz',
                   '--mymodule-lastrun=2012-09-18T15:41:00', # 'T' is a new feature
                   '--mymodule-arbitrary-nesting-depth=works']

        cfg = LayeredConfig(Commandline(cmdline))
        self._test_subsections(cfg,
                               int_type=str,
                               bool_type=str,
                               list_type=list,
                               date_type=str,
                               datetime_type=str)


class TestTyping(unittest.TestCase):

    def test_typed_inifile(self):
        types = {'home':str,
                 'processes':int,
                 'force':bool,
                 'extra':list, 
                 'mymodule':{'force':bool,
                             'lastrun':datetime}}

        cfg = LayeredConfig(Defaults(types),INIFile("ferenda.ini"))
        # cfg = LayeredConfig(inifile="ferenda.ini")
        self.assertEqual(cfg.home,'mydata')
        self.assertIs(type(cfg.home),str)
        self.assertEqual(cfg.processes,4)
        self.assertIs(type(cfg.processes),int)
        self.assertEqual(cfg.force,True)
        self.assertIs(type(cfg.force),bool)
        self.assertEqual(cfg.extra,['foo','bar'])
        self.assertIs(type(cfg.extra),list)
        self.assertEqual(cfg.mymodule.force,False)
        self.assertIs(type(cfg.mymodule.force),bool)
        self.assertEqual(cfg.mymodule.lastrun,datetime(2012,9,18,15,41,0))
        self.assertIs(type(cfg.mymodule.lastrun),datetime)

        
    def test_typed_commandline(self):
        types = {'home':str,
                 'processes':int,
                 'force':bool,
                 'extra':list, 
                 'mymodule':{'force':bool,
                             'lastrun':datetime}
                 }

        cmdline = ['--home=mydata',
                   '--processes=4',
                   '--force=True',
                   '--extra=foo',
                   '--extra=bar',
                   '--mymodule-force=False',
                   '--mymodule-lastrun=2012-09-18 15:41:00']
        cfg = LayeredConfig(Defaults(types), Commandline(cmdline))
        self.assertEqual(cfg.home,'mydata')
        self.assertIs(type(cfg.home),str)
        self.assertEqual(cfg.processes,4)
        self.assertIs(type(cfg.processes),int)
        self.assertEqual(cfg.force,True)
        self.assertIs(type(cfg.force),bool)
        self.assertEqual(cfg.extra,['foo','bar'])
        self.assertIs(type(cfg.extra),list)
        self.assertEqual(cfg.mymodule.force,False)
        self.assertIs(type(cfg.mymodule.force),bool)
        self.assertEqual(cfg.mymodule.lastrun,datetime(2012,9,18,15,41,0))
        self.assertIs(type(cfg.mymodule.lastrun),datetime)

        # make sure this auto-typing isn't run for bools
        types = {'logfile': True}
        cmdline = ["--logfile=out.log"]
        cfg = LayeredConfig(Defaults(types),Commandline(cmdline))
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
        cfg = LayeredConfig(INIFile("ferenda.ini"))
        LayeredConfig.set(cfg, 'lastrun', datetime(2013, 9, 18, 15, 41, 0),
                          "defaults")
        self.assertEqual(datetime(2013, 9, 18, 15, 41, 0), cfg.lastrun)
        self.assertFalse(cfg._inifile_dirty)

    def test_get(self):
        pass
        

if __name__ == '__main__':
    unittest.main()
