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
import sys
import codecs
from six import text_type as str
from datetime import date, datetime
import argparse
import json
from operator import itemgetter
from copy import deepcopy
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    # if on python 2.6
    from ordereddict import OrderedDict

if sys.version_info < (2, 7, 0):  # pragma: no cover
    import unittest2 as unittest
else:
    import unittest
import requests
# The system under test
from layeredconfig import (LayeredConfig, Defaults, INIFile, JSONFile,
                           YAMLFile, PListFile, PyFile, Environment,
                           Commandline, EtcdStore)


class TestLayeredConfigHelper(object):

    # Testcases for less-capable sources may override this
    supported_types = (str, int, bool, list, date, datetime)
    supports_nesting = True

    def _test_config_singlesection(self, cfg):
        self.assertIs(type(cfg.home), str)
        self.assertEqual(cfg.home, 'mydata')

        int_type = int if int in self.supported_types else str
        self.assertIs(type(cfg.processes), int_type)
        self.assertEqual(cfg.processes, int_type(4))

        if bool in self.supported_types:
            self.assertEqual(cfg.force, True)
        else:
            self.assertEqual(cfg.force, "True")

        if list in self.supported_types:
            list_type = list
            list_want = ['foo', 'bar']
            self.assertIs(type(cfg.extra[0]), str)
        else:
            list_type = str
            list_want = "foo, bar"  # recommended list serialization
        self.assertIs(type(cfg.extra), list_type)
        self.assertEqual(cfg.extra, list_want)

        if date in self.supported_types:
            date_type = date
            date_want = date(2014, 10, 15)
        else:
            date_type = str
            date_want = "2014-10-15" # recommended date serialization
        self.assertIs(type(cfg.expires), date_type)
        self.assertEqual(cfg.expires, date_want)

        if datetime in self.supported_types:
            datetime_type = datetime
            datetime_want = datetime(2014, 10, 15, 14, 32, 7)
        else:
            datetime_type = str
            datetime_want = "2014-10-15 14:32:07"
        self.assertIs(type(cfg.lastrun), datetime_type)
        self.assertEqual(cfg.lastrun, datetime_want)

    def _test_config_subsections(self, cfg):
        self.assertEqual(cfg.home, 'mydata')
        with self.assertRaises(AttributeError):
            cfg.mymodule.home

        int_type = int if int in self.supported_types else str
        self.assertEqual(cfg.processes, int_type(4))
        with self.assertRaises(AttributeError):
            cfg.mymodule.processes

        if bool in self.supported_types:
            self.assertEqual(cfg.mymodule.force, False)
        else:
            self.assertEqual(cfg.mymodule.force, "False")

        if list in self.supported_types:
            list_type = list
            list_want = ['foo', 'bar']
            list_want_sub = ['foo', 'baz']
        else:
            list_type = str
            list_want = "foo, bar"
            list_want_sub = "foo, baz"
        self.assertEqual(cfg.extra, list_want)
        self.assertEqual(cfg.mymodule.extra, list_want_sub)

        # not supported for INIFile
        if self.supports_nesting:
            self.assertEqual(cfg.mymodule.arbitrary.nesting.depth, 'works')

        with self.assertRaises(AttributeError):
            cfg.expires

        if date in self.supported_types:
            date_type = date
            date_want = date(2014, 10, 15)
        else:
            date_type = str
            date_want = "2014-10-15" # recommended date serialization
        self.assertEqual(cfg.mymodule.expires, date_want)

    def _test_layered_configs(self, cfg):
        self.assertEqual(cfg.home, 'otherdata')

        bool_type = bool if bool in self.supported_types else str
        self.assertEqual(cfg.mymodule.force, bool_type(False))

    def _test_layered_subsection_configs(self, cfg):
        if date in self.supported_types:
            date_type = date
            date_want = date(2014, 10, 15)
        else:
            date_type = str
            date_want = "2014-10-15" # recommended date serialization
        self.assertIs(type(cfg.mymodule.expires), date_type)
        self.assertEqual(cfg.mymodule.expires, date_want)


class TestConfigSourceHelper(TestLayeredConfigHelper):

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
        # FIXME: This test should be able to look at supported_types
        # like test_singlesection and test_subsections do, so derived
        # testcase classes don't need to override it.
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
    def test_config_singlesection(self):
        # each subclass is responsible for creating a self.simple
        # object of the type being tested
        cfg = LayeredConfig(self.simple)
        self._test_config_singlesection(cfg)

    def test_config_subsections(self):
        cfg = LayeredConfig(self.complex)
        self._test_config_subsections(cfg)

    def test_layered_subsections(self):
        # this testcases excercies a bug (or rather a deficency in the
        # file-based sources) -- if the highest-priority source has
        # subsections, and a lower-priority file-based source lacks
        # those subsections, bad things would happen.
        #
        # see https://github.com/staffanm/layeredconfig/issues/2
        cfg = LayeredConfig(self.complex, self.extra)
        self._test_layered_configs(cfg)

    def test_overwriting_with_missing_subsections(self):
        # this testcase tests the inverse of test_layered_subsections
        cfg = LayeredConfig(self.complex, self.extra_layered)
        self._test_layered_subsection_configs(cfg)
        
    DUMP_DEFAULTS = {'processes': int,
                     'force': bool,
                     'extra': list,
                     'mymodule': {
                         'force': bool,
                         'extra': list,
                         'expires': date,
                     },
                     'extramodule': {
                         'unique': bool
                     }
    }
    DUMP_WANT = {'home': 'mydata',
                 'processes': 4,
                 'force': True,
                 'extra': ['foo', 'bar'],
                 'mymodule': {
                     'force': False,
                     'extra': ['foo', 'baz'],
                     'expires': date(2014, 10, 15),
                     'arbitrary': {
                        'nesting': {
                            'depth': 'works'
                        }
                    }
                 },
                 'extramodule': {
                     'unique': True
                 }
    } 
    def test_dump(self):
        want = deepcopy(self.DUMP_WANT)
        if not self.supports_nesting:
            # INIFile does not support nested sections
            del want['mymodule']['arbitrary']
        cfg = LayeredConfig(Defaults(self.DUMP_DEFAULTS), self.complex)
        got = LayeredConfig.dump(cfg)
        self.maxDiff = None
        self.assertEquals(want, got)

    
    def test_dump_layered(self):
        want = deepcopy(self.DUMP_WANT)
        if not self.supports_nesting:
            # INIFile does not support nested sections
            del want['mymodule']['arbitrary']
        want['home'] = 'otherdata'
        cfg = LayeredConfig(Defaults(self.DUMP_DEFAULTS), self.complex, self.extra)
        got = LayeredConfig.dump(cfg)
        self.maxDiff = None
        self.assertEquals(want, got)

    

# common helper
class TestINIFileHelper(object):

    def setUp(self):
        super(TestINIFileHelper, self).setUp()
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
force = False
extra = foo, baz
expires = 2014-10-15

[extramodule]
unique = True
""")

        with open("extra.ini", "w") as fp:
            fp.write("""
[__root__]
home = otherdata
""")

        with open("extra-layered.ini", "w") as fp:
            fp.write("""
[mymodule]
expires = 2014-10-15
""")



    def tearDown(self):
        super(TestINIFileHelper, self).tearDown()
        os.unlink("simple.ini")
        os.unlink("complex.ini")
        os.unlink("extra.ini")
        os.unlink("extra-layered.ini")


class TestDefaults(unittest.TestCase, TestConfigSourceHelper):

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

    extra = Defaults({'home': 'otherdata'})

    extra_layered = Defaults({'mymodule': {'force': True}})

class TestINIFile(TestINIFileHelper, unittest.TestCase,
                  TestConfigSourceHelper):

    supported_types = (str,)
    supports_nesting = False

    def setUp(self):
        super(TestINIFile, self).setUp()
        self.simple = INIFile("simple.ini")
        self.complex = INIFile("complex.ini")
        self.extra = INIFile("extra.ini")
        self.extra_layered = INIFile("extra-layered.ini")

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

    # Override: INIFile doesn't support nested subsections
    def test_subsection_nested(self):
        subsec = self.complex.subsection('mymodule')
        self.assertEqual(set(subsec.subsections()),
                         set(()))

    def test_inifile_default_as_root(self):
        # using a rootsection named DEFAULT triggers different
        # cascading-like behaviour in configparser.

        # load a modified version of complex.ini
        with open("complex.ini") as fp:
            ini = fp.read()

        with open("complex-otherroot.ini", "w") as fp:
            fp.write(ini.replace("[__root__]", "[DEFAULT]"))
        cfg = LayeredConfig(INIFile("complex-otherroot.ini",
                                    rootsection="DEFAULT"))

        # this is a modified/simplified version of ._test_subsections
        self.assertEqual(cfg.home, 'mydata')
        self.assertEqual(cfg.processes, '4')
        self.assertEqual(cfg.force, 'True')
        self.assertEqual(cfg.mymodule.force, 'False')
        self.assertEqual(cfg.extra, "foo, bar")
        self.assertEqual(cfg.mymodule.extra, "foo, baz")
        with self.assertRaises(AttributeError):
            cfg.expires
        self.assertEqual(cfg.mymodule.expires, "2014-10-15")

        # this is really unwanted cascading behaviour
        self.assertEqual(cfg.mymodule.home, 'mydata')
        self.assertEqual(cfg.mymodule.processes, '4')

        os.unlink("complex-otherroot.ini")

    def test_inifile_nonexistent(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        cfg = LayeredConfig(INIFile("nonexistent.ini"))
        self.assertEqual([], list(cfg))

        # make sure a nonexistent inifile doesn't interfere with the
        # rest of the LayeredConfig object
        defobj = Defaults({'datadir': 'something'})
        iniobj = INIFile("nonexistent.ini")
        cfg = LayeredConfig(defobj, iniobj)
        self.assertEqual("something", cfg.datadir)

        # and make sure it's settable (should set up the INIFile
        # object and affect it, and leave the defaults dict untouched
        # as it's the lowest priority)
        cfg.datadir = "else"
        self.assertEqual("else", cfg.datadir)
        self.assertEqual("else", iniobj.get("datadir"))
        self.assertEqual("something", defobj.get("datadir"))

        # same as above, but with a "empty" INIFile object
        iniobj = INIFile()
        cfg = LayeredConfig(defobj, iniobj)
        self.assertEqual("something", cfg.datadir)
        cfg.datadir = "else"
        self.assertEqual("else", cfg.datadir)

    def test_write(self):
        cfg = LayeredConfig(INIFile("complex.ini"))
        cfg.mymodule.expires = date(2014, 10, 24)
        cfg.mymodule.extra = ['foo', 'baz', 'quux']
        # calling write for any submodule will force a write of the
        # entire config file
        LayeredConfig.write(cfg.mymodule)
        want = """[__root__]
home = mydata
processes = 4
force = True
extra = foo, bar

[mymodule]
force = False
extra = foo, baz, quux
expires = 2014-10-24

[extramodule]
unique = True

"""
        with open("complex.ini") as fp:
            got = fp.read().replace("\r\n", "\n")
        self.assertEqual(want, got)


class TestJSONFile(unittest.TestCase, TestConfigSourceHelper):

    supported_types = (str, int, bool, list)

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
        with open("extra.json", "w") as fp:
            fp.write('{"home": "otherdata"}')

        with open("extra-layered.json", "w") as fp:
            fp.write('{"mymodule": {"force": true}}')

        self.simple = JSONFile("simple.json")
        self.complex = JSONFile("complex.json")
        self.extra = JSONFile("extra.json")
        self.extra_layered = JSONFile("extra-layered.json")

    def tearDown(self):
        os.unlink("simple.json")
        os.unlink("complex.json")
        os.unlink("extra.json")
        os.unlink("extra-layered.json")

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

    def test_write(self):
        self.maxDiff = None
        cfg = LayeredConfig(self.complex)
        cfg.mymodule.expires = date(2014, 10, 24)
        cfg.mymodule.extra.append("quux")
        # calling write for any submodule will force a write of the
        # entire config file
        LayeredConfig.write(cfg.mymodule)
        want = """{
    "extra": [
        "foo",
        "bar"
    ],
    "extramodule": {
        "unique": true
    },
    "force": true,
    "home": "mydata",
    "mymodule": {
        "arbitrary": {
            "nesting": {
                "depth": "works"
            }
        },
        "expires": "2014-10-24",
        "extra": [
            "foo",
            "baz",
            "quux"
        ],
        "force": false
    },
    "processes": 4
}"""
        with open("complex.json") as fp:
            got = fp.read().replace("\r\n", "\n")
        self.assertEqual(want, got)

class TestYAMLFile(unittest.TestCase,
                   TestConfigSourceHelper):
    def setUp(self):
        with open("simple.yaml", "w") as fp:
            fp.write("""
home: mydata
processes: 4
force: true
extra:
- foo
- bar
expires: 2014-10-15
lastrun: 2014-10-15 14:32:07
""")
        with open("complex.yaml", "w") as fp:
            fp.write("""
home: mydata
processes: 4
force: true
extra:
- foo
- bar
mymodule:
    force: false
    extra:
    - foo
    - baz
    expires: 2014-10-15
    arbitrary:
        nesting:
            depth: works
extramodule:
    unique: true
""")
        with open("extra.yaml", "w") as fp:
            fp.write("""
home: otherdata
""")

        with open("extra-layered.yaml", "w") as fp:
            fp.write("""
mymodule:
    force: true        
""")
                     
        self.simple = YAMLFile("simple.yaml")
        self.complex = YAMLFile("complex.yaml")
        self.extra = YAMLFile("extra.yaml")
        self.extra_layered = YAMLFile("extra-layered.yaml")

    def tearDown(self):
        os.unlink("simple.yaml")
        os.unlink("complex.yaml")
        os.unlink("extra.yaml")
        os.unlink("extra-layered.yaml")

    # Also, strings are unicode when they need to be,
    # str otherwise.
    def test_i18n(self):
        with codecs.open("i18n.yaml", "w", encoding="utf-8") as fp:
            fp.write("shrimpsandwich: Räksmörgås")
        cfg = LayeredConfig(YAMLFile("i18n.yaml"))
        self.assertEqual("Räksmörgås", cfg.shrimpsandwich)
        os.unlink("i18n.yaml")

    def test_write(self):
        cfg = LayeredConfig(self.complex)
        cfg.mymodule.expires = date(2014, 10, 24)
        cfg.mymodule.extra.append('quux')
        # calling write for any submodule will force a write of the
        # entire config file
        LayeredConfig.write(cfg.mymodule)
        # note that pyyaml sorts keys alphabetically and has specific
        # ideas on how to format the result (controllable through
        # mostly-undocumented args to dump())
        want = """
extra:
- foo
- bar
extramodule:
  unique: true
force: true
home: mydata
mymodule:
  arbitrary:
    nesting:
      depth: works
  expires: 2014-10-24
  extra:
  - foo
  - baz
  - quux
  force: false
processes: 4
""".lstrip()
        with open("complex.yaml") as fp:
            got = fp.read().replace("\r\n", "\n")
        self.assertEqual(want, got)


class TestPListFile(unittest.TestCase, TestConfigSourceHelper):

    supported_types = (str, int, bool, list, datetime)

    def setUp(self):
        with open("simple.plist", "w") as fp:
            fp.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>expires</key>
        <string>2014-10-15</string>
        <key>extra</key>
        <array>
                <string>foo</string>
                <string>bar</string>
        </array>
        <key>force</key>
        <true/>
        <key>home</key>
        <string>mydata</string>
        <key>lastrun</key>
        <date>2014-10-15T14:32:07Z</date>
        <key>processes</key>
        <integer>4</integer>
</dict>
</plist>
""")
        with open("complex.plist", "w") as fp:
            fp.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>extra</key>
        <array>
                <string>foo</string>
                <string>bar</string>
        </array>
        <key>extramodule</key>
        <dict>
                <key>unique</key>
                <true/>
        </dict>
        <key>force</key>
        <true/>
        <key>home</key>
        <string>mydata</string>
        <key>mymodule</key>
        <dict>
                <key>arbitrary</key>
                <dict>
                        <key>nesting</key>
                        <dict>
                                <key>depth</key>
                                <string>works</string>
                        </dict>
                </dict>
                <key>expires</key>
                <string>2014-10-15</string>
                <key>extra</key>
                <array>
                        <string>foo</string>
                        <string>baz</string>
                </array>
                <key>force</key>
                <false/>
        </dict>
        <key>processes</key>
        <integer>4</integer>
</dict>
</plist>
""")
        with open("extra.plist", "w") as fp:
            fp.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>home</key>
        <string>otherdata</string>
</dict>
</plist>
""")

        with open("extra-layered.plist", "w") as fp:
            fp.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>mymodule</key>
        <dict>
                <key>force</key>
                <true/>
        </dict>
</dict>
</plist>
""")
        self.simple = PListFile("simple.plist")
        self.complex = PListFile("complex.plist")
        self.extra = PListFile("extra.plist")
        self.extra_layered = PListFile("extra-layered.plist")

    def tearDown(self):
        os.unlink("simple.plist")
        os.unlink("complex.plist")
        os.unlink("extra.plist")
        os.unlink("extra-layered.plist")

    # override only because plists cannot handle date objects (only datetime)
    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), 4)
        self.assertEqual(self.simple.get("force"), True)
        self.assertEqual(self.simple.get("extra"), ['foo', 'bar'])
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"),
                         datetime(2014, 10, 15, 14, 32, 7))

    def test_write(self):
        self.maxDiff = None
        cfg = LayeredConfig(self.complex)
        cfg.mymodule.expires = date(2014, 10, 24)
        cfg.mymodule.extra.append('quux')
        # calling write for any submodule will force a write of the
        # entire config file
        LayeredConfig.write(cfg.mymodule)
        # note: plistlib creates files with tabs, not spaces.
        want = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>extra</key>
	<array>
		<string>foo</string>
		<string>bar</string>
	</array>
	<key>extramodule</key>
	<dict>
		<key>unique</key>
		<true/>
	</dict>
	<key>force</key>
	<true/>
	<key>home</key>
	<string>mydata</string>
	<key>mymodule</key>
	<dict>
		<key>arbitrary</key>
		<dict>
			<key>nesting</key>
			<dict>
				<key>depth</key>
				<string>works</string>
			</dict>
		</dict>
		<key>expires</key>
		<string>2014-10-24</string>
		<key>extra</key>
		<array>
			<string>foo</string>
			<string>baz</string>
			<string>quux</string>
		</array>
		<key>force</key>
		<false/>
	</dict>
	<key>processes</key>
	<integer>4</integer>
</dict>
</plist>
"""
        if sys.version_info < (2,7,0): # pragma: no cover
            # on py26, the doctype includes "Apple Computer" not "Apple"...
            want = want.replace("//Apple//", "//Apple Computer//")
        with open("complex.plist") as fp:
            got = fp.read().replace("\r\n", "\n")
        self.assertEqual(want, got)

    def test_typed(self):
        for key in self.simple.keys():
            # PList can type ints, bools, lists and datetimes (but not dates)
            if key in ("processes", "force", "extra", "lastrun"):
                self.assertTrue(self.simple.typed(key))
            else:
                self.assertFalse(self.simple.typed(key))


class TestPyFile(unittest.TestCase, TestConfigSourceHelper):

    def setUp(self):
        with open("simple.py", "w") as fp:
            fp.write("""from __future__ import unicode_literals
import datetime

expires = datetime.date(2014,10,15)
extra = ['foo', 'bar']
force = True
home = 'mydata'
lastrun = datetime.datetime(2014,10,15,14,32,7)
processes = 4
""")
        with open("complex.py", "w") as fp:
            fp.write("""from __future__ import unicode_literals
import datetime

extra = ['foo', 'bar']
force = True
home = 'mydata'
processes = 4

mymodule = Subsection()
mymodule.expires = datetime.date(2014,10,15)
mymodule.extra = ['foo', 'baz']
mymodule.force = False
mymodule.arbitrary = Subsection()
mymodule.arbitrary.nesting = Subsection()
mymodule.arbitrary.nesting.depth = 'works'

extramodule = Subsection()
extramodule.unique = True
""")

        with open("extra.py", "w") as fp:
            fp.write("""from __future__ import unicode_literals

home = 'otherdata'
""")

        with open("extra-layered.py", "w") as fp:
            fp.write("""from __future__ import unicode_literals

mymodule = Subsection()
mymodule.force = True
""")
        self.simple = PyFile("simple.py")
        self.complex = PyFile("complex.py")
        self.extra = PyFile("extra.py")
        self.extra_layered = PyFile("extra-layered.py")

    def tearDown(self):
        os.unlink("simple.py")
        os.unlink("complex.py")
        os.unlink("extra.py")
        os.unlink("extra-layered.py")


class TestCommandline(unittest.TestCase, TestConfigSourceHelper):

    # Note: bool is "half-way" supported. Only value-less parameters
    # are typed as bool (eg "--force", not "--force=True")
    supported_types = (str, list, bool)

    simple_cmdline = ['--home=mydata',
                      '--processes=4',
                      '--force',  # note implicit boolean typing
                      '--extra=foo',
                      '--extra=bar',
                      '--expires=2014-10-15',
                      '--lastrun=2014-10-15 14:32:07']

    complex_cmdline = ['--home=mydata',
                       '--processes=4',
                       '--force=True',
                       '--extra=foo',
                       '--extra=bar',
                       '--mymodule-force=False',
                       '--mymodule-extra=foo',
                       '--mymodule-extra=baz',
                       '--mymodule-expires=2014-10-15',
                       '--mymodule-arbitrary-nesting-depth=works',
                       '--extramodule-unique']

    def setUp(self):
        super(TestCommandline, self).setUp()
        # this means we lack typing information
        self.simple = Commandline(self.simple_cmdline)
        self.complex = Commandline(self.complex_cmdline)


    # Overrides of TestHelper.test_get, .test_typed and and due to
    # limitations of Commandline (carries almost no typeinfo)
    def test_get(self):
        self.assertEqual(self.simple.get("home"), "mydata")
        self.assertEqual(self.simple.get("processes"), "4")
        self.assertEqual(self.simple.get("force"), True)
        self.assertEqual(self.simple.get("extra"), ['foo','bar'])  # note typed!
        self.assertEqual(self.simple.get("expires"), "2014-10-15")
        self.assertEqual(self.simple.get("lastrun"), "2014-10-15 14:32:07")

    def test_typed(self):
        for key in self.simple.keys():
            # these should be typed as bool and list, respectively
            if key in ("force", "extra"):
                self.assertTrue(self.simple.typed(key))
            else:
                self.assertFalse(self.simple.typed(key))


    def test_config_subsections(self):
        # this case uses valued parameter for --force et al, which
        # cannot be reliably converted to bools using only intrinsic
        # information
        self.supported_types = (str, list)
        super(TestCommandline, self).test_config_subsections()

    def test_layered_subsections(self):
        pass  # this test has no meaning for Command line arguments
              # (can't have two sets of them)

    def test_overwriting_with_missing_subsections(self):
        pass  # this test has no meaning for Command line arguments
              # (can't have two sets of them)

    def test_dump_layered(self):
        pass

    def test_set(self):
        self.simple.set("home", "away from home")
        self.assertEqual(self.simple.get("home"), "away from home")


class TestCommandlineConfigured(TestCommandline):

    supported_types = (str, int, bool, date, datetime, list)

    def setUp(self):
        super(TestCommandlineConfigured, self).setUp()
        simp = argparse.ArgumentParser(description="This is a simple program")
        simp.add_argument('--home', help="The home directory of the app")
        simp.add_argument('--processes', type=int, help="Number of simultaneous processes")
        simp.add_argument('--force', type=LayeredConfig.boolconvert, nargs='?', const=True)
        simp.add_argument('--extra', action='append')
        simp.add_argument('--expires', type=LayeredConfig.dateconvert)
        simp.add_argument('--lastrun', type=LayeredConfig.datetimeconvert)
        simp.add_argument('--unused')
        self.simple = Commandline(self.simple_cmdline,
                                  parser=simp)

        comp = argparse.ArgumentParser(description="This is a complex program")
        comp.add_argument('--home', help="The home directory of the app")
        comp.add_argument('--processes', type=int, help="Number of simultaneous processes")
        comp.add_argument('--force', type=LayeredConfig.boolconvert, nargs='?', const=True)
        comp.add_argument('--extra', action='append')
        comp.add_argument('--mymodule-force', type=LayeredConfig.boolconvert, nargs='?', const=True)
        comp.add_argument('--mymodule-extra', action='append')
        comp.add_argument('--mymodule-expires', type=LayeredConfig.dateconvert)
        comp.add_argument('--mymodule-arbitrary-nesting-depth')
        comp.add_argument('--extramodule-unique', nargs='?', const=True)
        self.complex = Commandline(self.complex_cmdline,
                                   parser=comp)

    def test_get(self):
        # re-enable the original impl of test_get
        TestConfigSourceHelper.test_get(self)

    def test_config_subsections(self):
        # re-enable the original impl of test_config_subsections
        TestConfigSourceHelper.test_config_subsections(self)

    def test_typed(self):
        # re-enable the original impl of test_get
        TestConfigSourceHelper.test_typed(self)


class TestEnvironment(unittest.TestCase, TestConfigSourceHelper):

    supported_types = (str,)

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
                           'MYAPP_MYMODULE_EXTRA': "foo, baz",
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

    def test_layered_subsections(self):
        pass  # this test has no meaning for environment variables
              # (can't have two sets of them)

    def test_overwriting_with_missing_subsections(self):
        pass  # this test has no meaning for environment variables
              # (can't have two sets of them)

    def test_dump_layered(self):
        pass

    def test_typed(self):
        for key in self.simple.keys():
            self.assertFalse(self.simple.typed(key))


# NB: This assumes that an etcd daemon is running with default
# settings
ETCD_BASE = "http://127.0.0.1:4001/v2/keys"

@unittest.skipIf("APPVEYOR" in os.environ,
                 "Not running etcd dependent tests on Appveyor")
class TestEtcdStore(unittest.TestCase, TestConfigSourceHelper):
    maxDiff = None
    def strlower(value):
        return str(value).lower()

    supported_types = (str,)

    def _clear_server(self):
        resp = requests.get(ETCD_BASE + "/")
        resp.raise_for_status()
        json = resp.json()
        if 'nodes' in json['node']:
            for node in json['node']['nodes']:
                resp = requests.delete(ETCD_BASE + "%s?recursive=true" % node['key'])

    @property
    def simple(self):
        self._clear_server()
        requests.put(ETCD_BASE + "/home", data={'value': 'mydata'})
        requests.put(ETCD_BASE + "/processes", data={'value': '4'})
        requests.put(ETCD_BASE + "/force", data={'value': "True"})
        requests.put(ETCD_BASE + "/extra", data={'value': "foo, bar"})
        requests.put(ETCD_BASE + "/expires", data={'value': "2014-10-15"})
        requests.put(ETCD_BASE + "/lastrun", data={'value': "2014-10-15 14:32:07"})
        return EtcdStore()

    @property
    def complex(self):
        self._clear_server()
        requests.put(ETCD_BASE + "/home", data={'value': "mydata"})
        requests.put(ETCD_BASE + "/processes", data={'value': "4"})
        requests.put(ETCD_BASE + "/force", data={'value': "True"})
        requests.put(ETCD_BASE + "/extra", data={'value': "foo, bar"})
        requests.put(ETCD_BASE + "/mymodule/force", data={'value': "False"})
        requests.put(ETCD_BASE + "/mymodule/extra", data={'value': "foo, baz"})
        requests.put(ETCD_BASE + "/mymodule/expires", data={'value': "2014-10-15"})
        requests.put(ETCD_BASE + "/mymodule/arbitrary/nesting/depth", data={'value': "works"})
        requests.put(ETCD_BASE + "/extramodule/unique", data={'value': "True"})
        return EtcdStore()

    def test_layered_subsections(self):
        pass  # this test has no meaning for etcd stores, as a single
              # server cannot have two sets of configuration to layere
              # (however, we could concievably have two distinct
              # servers -- but that isn't supported on ground of being
              # too complicated)

    def test_overwriting_with_missing_subsections(self):
        pass  # ditto

    def test_dump_layered(self):
        pass

    def test_typed(self):
        for key in self.simple.keys():
            self.assertFalse(self.simple.typed(key))

    def test_get(self):
        # FIXME: This test should be able to look at supported_types
        # like test_singlesection and test_subsections do, so derived
        # testcase classes don't need to override it.
        conf = self.simple
        self.assertEqual(conf.get("home"), "mydata")
        self.assertEqual(conf.get("processes"), "4")
        self.assertEqual(conf.get("force"), "True")
        self.assertEqual(conf.get("extra"), "foo, bar")
        self.assertEqual(conf.get("expires"), "2014-10-15")
        self.assertEqual(conf.get("lastrun"), "2014-10-15 14:32:07")

    def test_write(self):
        def indexfilter(node):
            # remove keys like createdIdex / modifiedIndex whose
            # values always changes
            if isinstance(node, dict):
                for key in list(node.keys()):
                    if key == "nodes":
                        indexfilter(node[key])
                    elif key.endswith("Index"):
                        del node[key]
            else:
                node[:] = sorted(node, key=itemgetter('key'))
                for subnode in node:
                    indexfilter(subnode)

        cfg = LayeredConfig(self.complex)
        cfg.extra = ['foo', 'value with space']
        cfg.mymodule.expires = date(2014, 10, 24)
        cfg.mymodule.extra = ['foo', 'baz', 'quux']
        # note that this will write the entire config incl cfg.extra,
        # not just the values in the 'mymodule' subsection.
        LayeredConfig.write(cfg.mymodule)
        want = """
{
    "dir": true,
    "nodes": [
        {
            "createdIndex": 4627,
            "key": "/home",
            "modifiedIndex": 4627,
            "value": "mydata"
        },
        {
            "createdIndex": 4628,
            "key": "/processes",
            "modifiedIndex": 4628,
            "value": "4"
        },
        {
            "createdIndex": 4629,
            "key": "/force",
            "modifiedIndex": 4629,
            "value": "True"
        },
        {
            "createdIndex": 4630,
            "key": "/extra",
            "modifiedIndex": 4630,
            "value": "['foo', 'value with space']"
        },
        {
            "createdIndex": 4631,
            "dir": true,
            "key": "/mymodule",
            "modifiedIndex": 4631,
            "nodes": [
                {
                    "createdIndex": 4631,
                    "key": "/mymodule/force",
                    "modifiedIndex": 4631,
                    "value": "False"
                },
                {
                    "createdIndex": 4632,
                    "key": "/mymodule/extra",
                    "modifiedIndex": 4632,
                    "value": "foo, baz, quux"
                },
                {
                    "createdIndex": 4633,
                    "key": "/mymodule/expires",
                    "modifiedIndex": 4633,
                    "value": "2014-10-24"
                },
                {
                    "createdIndex": 4634,
                    "dir": true,
                    "key": "/mymodule/arbitrary",
                    "modifiedIndex": 4634,
                    "nodes": [
                        {
                            "createdIndex": 4634,
                            "dir": true,
                            "key": "/mymodule/arbitrary/nesting",
                            "modifiedIndex": 4634,
                            "nodes": [
                                {
                                    "createdIndex": 4634,
                                    "key": "/mymodule/arbitrary/nesting/depth",
                                    "modifiedIndex": 4634,
                                    "value": "works"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "createdIndex": 4635,
            "dir": true,
            "key": "/extramodule",
            "modifiedIndex": 4635,
            "nodes": [
                {
                    "createdIndex": 4635,
                    "key": "/extramodule/unique",
                    "modifiedIndex": 4635,
                    "value": "True"
                }
            ]
        }
    ]
}"""
        want = json.loads(want)
        indexfilter(want)
        got = requests.get("http://localhost:4001/v2/keys/?recursive=true").json()['node']
        indexfilter(got)
        self.assertEqual(want, got)


class TestTyping(unittest.TestCase, TestLayeredConfigHelper):
    types = {'home': str,
             'processes': int,
             'force': bool,
             'extra': list,
             'mymodule': {'force': bool,
                          'extra': list,
                          'expires': date,
                          'lastrun': datetime,
                      }
             }

    def test_typed_commandline(self):
        cmdline = ['--home=mydata',
                   '--processes=4',
                   '--force=True',
                   '--extra=foo',
                   '--extra=bar',
                   '--implicitboolean',
                   '--mymodule-force=False',
                   '--mymodule-extra=foo',
                   '--mymodule-extra=baz',
                   '--mymodule-expires=2014-10-15',
                   '--mymodule-arbitrary-nesting-depth=works',
                   '--extramodule-unique']
        cfg = LayeredConfig(Defaults(self.types), Commandline(cmdline))
        self._test_config_subsections(cfg)
        self.assertTrue(cfg.implicitboolean)
        self.assertIs(type(cfg.implicitboolean), bool)

    def test_typed_novalue(self):
        # this cmdline only sets some of the settings. The test is
        # that the rest should raise AttributeError (not return None,
        # as was the previous behaviour), and that __iter__ should not
        # include them.
        cmdline = ['--processes=4', '--force=False']
        cfg = LayeredConfig(Defaults(self.types), Commandline(cmdline))
        self.assertEqual(4, cfg.processes)
        self.assertIsInstance(cfg.processes, int)
        with self.assertRaises(AttributeError):
            cfg.home
        with self.assertRaises(AttributeError):
            cfg.extra
        self.assertEqual(set(['processes', 'force']),
                         set(list(cfg)))

    def test_typed_override(self):
        # make sure this auto-typing isn't run for bools
        types = {'logfile': True}
        cmdline = ["--logfile=out.log"]
        cfg = LayeredConfig(Defaults(types), Commandline(cmdline))
        self.assertEqual(cfg.logfile, "out.log")

    def test_typed_commandline_cascade(self):
        # the test here is that __getattribute__ must determine that
        # subconfig.force is not typed in itself, and fetch type
        # information from the root of defaults

        defaults = {'force': True,
                    'lastdownload': datetime,
                    'mymodule': {}}
        cmdline = ['--mymodule-force=False']
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline),
                            cascade=True)
        subconfig = getattr(cfg, 'mymodule')
        self.assertIs(type(subconfig.force), bool)
        self.assertEqual(subconfig.force, False)

        # test typed config values that have no actual value. Since
        # they have no value, they should raise AtttributeError
        with self.assertRaises(AttributeError):
            self.assertEqual(cfg.lastdownload, None)
        with self.assertRaises(AttributeError):
            self.assertEqual(subconfig.lastdownload, None)

    def test_commandline_implicit_typing(self):
        # The big test here is really the partially-configured
        # ArgumentParser (handles one positional argument but not the
        # optional --force)
        defaults = {'force': False}
        cmdline = ['command', '--force']
        parser = argparse.ArgumentParser()
        parser.add_argument("positional")
        cmdlinesrc = Commandline(cmdline, parser=parser)
        cfg = LayeredConfig(Defaults(defaults), cmdlinesrc)
        self.assertEqual(cfg.force, True)

        # try again with explicit argument
        parser = argparse.ArgumentParser()
        parser.add_argument("positional")
        cmdlinesrc = Commandline(['command', '--force=True'], parser=parser)
        cfg = LayeredConfig(Defaults(defaults), cmdlinesrc)
        self.assertEqual(cfg.force, True)

        # once again without the optional typing source
        parser = argparse.ArgumentParser()
        parser.add_argument("positional")
        cmdlinesrc = Commandline(['command', '--force'], parser=parser)
        cfg = LayeredConfig(Defaults({}), cmdlinesrc)
        self.assertEqual(cfg.force, True)

    def test_layered_typing_for_none_values_in_lower_priority(self):
        source1 = Defaults({'key': None})
        source2 = Environment({'KEY': 3})
        config = LayeredConfig(source1, source2)
        self.assertEquals(config.key, 3)


class TestTypingINIFile(TestINIFileHelper,
                        TestLayeredConfigHelper,
                        unittest.TestCase):
    types = {'home': str,
             'processes': int,
             'force': bool,
             'extra': list,
             'mymodule': {'force': bool,
                          'extra': list,
                          'expires': date,
                          'lastrun': datetime,
                      }
             }

    # FIXME: find a neat way to run the tests in
    # test_config_subsections with a LayeredConfig object that uses a
    # Default object for typing
    def test_typed_inifile(self):
        cfg = LayeredConfig(Defaults(self.types), INIFile("complex.ini"))
        self.supported_types = (str, bool, int, list, date, datetime)
        self.supports_nesting = False
        self._test_config_subsections(cfg)


class TestLayered(TestINIFileHelper, unittest.TestCase):
    def test_layered(self):
        defaults = {'home': 'someplace'}
        cmdline = ['--home=anotherplace']
        env = {'MYAPP_HOME': 'yourdata'}
        cfg = LayeredConfig(Defaults(defaults))
        self.assertEqual(cfg.home, 'someplace')
        cfg = LayeredConfig(Defaults(defaults), INIFile("simple.ini"))
        self.assertEqual(cfg.home, 'mydata')
        cfg = LayeredConfig(Defaults(defaults), INIFile("simple.ini"),
                            Environment(env, prefix="MYAPP_"))
        self.assertEqual(cfg.home, 'yourdata')
        cfg = LayeredConfig(Defaults(defaults), INIFile("simple.ini"),
                            Environment(env, prefix="MYAPP_"),
                           Commandline(cmdline))
        self.assertEqual(cfg.home, 'anotherplace')
        self.assertEqual(['home', 'processes', 'force', 'extra', 'expires',
                          'lastrun'], list(cfg))

    def test_layered_subsections(self):
        defaults = OrderedDict((('force', False),
                                ('home', 'thisdata'),
                                ('loglevel', 'INFO')))
        cmdline = ['--mymodule-home=thatdata', '--mymodule-force']
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline),
                            cascade=True)
        self.assertEqual(cfg.mymodule.force, True)
        self.assertEqual(cfg.mymodule.home, 'thatdata')
        self.assertEqual(cfg.mymodule.loglevel, 'INFO')

        # second test is more difficult: the lower-priority Defaults
        # source only contains a subsection, while the higher-priority
        # Commandline source contains no such subsection. Our
        # sub-LayeredConfig object will only have a Defaults source,
        # not a Commandline source (which will cause the
        # __getattribute__ lookup_resource to look in the Defaults
        # object in the sub-LayeredConfig object, unless we do
        # something smart.
        defaults = {'mymodule': defaults}
        cmdline = ['--home=thatdata', '--force']

        o = Commandline(cmdline)
        o.subsection("mymodule").keys()
        cfg = LayeredConfig(Defaults(defaults), Commandline(cmdline),
                            cascade=True)
        self.assertEqual(cfg.mymodule.force, True)
        self.assertEqual(cfg.mymodule.home, 'thatdata')
        self.assertEqual(cfg.mymodule.loglevel, 'INFO')
        self.assertEqual(['force', 'home', 'loglevel'], list(cfg.mymodule))


class TestSubsections(unittest.TestCase):
    def test_list(self):
        defaults = {'home': 'mydata',
                    'subsection': {'processes': 4}}
        cfg = LayeredConfig(Defaults(defaults),
                            cascade=True)
        self.assertEqual(set(['home', 'processes']),
                         set(cfg.subsection))

    def test_subsection_respects_subclass(self):
        defaults = {
            'subsection': {
                'processes': 4
            }
        }

        class SubclassedLayeredConfig(LayeredConfig):
            pass

        cfg = SubclassedLayeredConfig(Defaults(defaults))
        self.assertIsInstance(cfg.subsection, SubclassedLayeredConfig)


class TestLayeredSubsections(unittest.TestCase):

    def _test_subsection(self, primary, secondary, cls):
        with open("primary.txt", "w") as fp:
            fp.write(primary)
        with open("secondary.txt", "w") as fp:
            fp.write(secondary)
        try:
            srcs = [cls('primary.txt'), cls('secondary.txt')]
            cfg = LayeredConfig(*srcs)
            self.assertEqual(cfg.somevar, 'value')
            self.assertEqual(cfg.a.b, 'b')
        finally:
            os.unlink("primary.txt")
            os.unlink("secondary.txt")

    def test_layered_yaml(self):
        self._test_subsection("""a:
  b: b
        """, "somevar: value", YAMLFile)

    def test_layered_ini(self):
        self._test_subsection("""
[__root__]

[a]

b = b
""", """
[__root__]
somevar = value
""", INIFile)

    def test_layered_json(self):
        self._test_subsection('{"a": {"b": "b"} }',
                              '{"somevar": "value"}',
                              JSONFile)

    def test_layered_plist(self):
        self._test_subsection("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>a</key>
        <dict>
        	<key>b</key>
        	<string>b</string>
        </dict>
</dict>
</plist>""", """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>somevar</key>
        <string>value</string>
</dict>
</plist>""", PListFile)



class TestModifications(TestINIFileHelper, unittest.TestCase):
    def test_modified(self):
        defaults = {'lastdownload': None}
        cfg = LayeredConfig(Defaults(defaults))
        now = datetime.now()
        cfg.lastdownload = now
        self.assertEqual(cfg.lastdownload, now)

    def test_modified_subsections(self):
        defaults = {'force': False,
                    'home': 'thisdata',
                    'loglevel': 'INFO'}
        cmdline = ['--mymodule-home=thatdata', '--mymodule-force']
        cfg = LayeredConfig(Defaults(defaults),
                            INIFile("complex.ini"),
                            Commandline(cmdline),
                            cascade=True)
        cfg.mymodule.expires = date(2014, 10, 24)

    def test_modified_singlesource_subsection(self):
        self.globalconf = LayeredConfig(
            Defaults({'download_text': None,
                      'base': {}}),
            cascade=True)
        # this should't raise an AttributeError
        self.globalconf.base.download_text
        # this shouldn't, either
        self.globalconf.base.download_text = "WHAT"

    def test_write_noconfigfile(self):
        cfg = LayeredConfig(Defaults({'lastrun':
                                      datetime(2012, 9, 18, 15, 41, 0)}))
        cfg.lastrun = datetime(2013, 9, 18, 15, 41, 0)
        LayeredConfig.write(cfg)

    def test_set_novalue(self):
        # it should be possible to set values that are defined in any
        # of the configsources, even though only typing information
        # exists there.
        cfg = LayeredConfig(Defaults({'placeholder': int}),
                            Commandline([]))
        cfg.placeholder = 42

        # but it shouldn't be possible to set values that hasn't been
        # defined anywhere.
        with self.assertRaises(AttributeError):
            cfg.nonexistent = 43


class TestAccessors(TestINIFileHelper, unittest.TestCase):

    def test_set(self):
        # a value is set in a particular underlying source, and the
        # dirty flag isn't set.
        cfg = LayeredConfig(INIFile("simple.ini"))
        LayeredConfig.set(cfg, 'expires', date(2013, 9, 18),
                          "inifile")
        # NOTE: For this config, where no type information is
        # available for key 'expires', INIFile.set will convert the
        # date object to a string, at which point typing is lost.
        # Therefore this commmented-out test will fail
        # self.assertEqual(date(2013, 9, 18), cfg.expires)
        self.assertEqual("2013-09-18", cfg.expires)
        self.assertFalse(cfg._sources[0].dirty)

    def test_get(self):
        cfg = LayeredConfig(Defaults({'codedefaults': 'yes',
                                      'force': False,
                                      'home': '/usr/home'}),
                            INIFile('simple.ini'))
        # and then do a bunch of get() calls with optional fallbacks
        self.assertEqual("yes", LayeredConfig.get(cfg, "codedefaults"))
        self.assertEqual("mydata", LayeredConfig.get(cfg, "home"))
        self.assertEqual(None, LayeredConfig.get(cfg, "nonexistent"))
        self.assertEqual("NO!", LayeredConfig.get(cfg, "nonexistent", "NO!"))


class TestDump(unittest.TestCase):
    def test_dump(self):
        defaults = {
            'home': 'mydata',
            'processes': 4,
            'force': True,
            'extra': ['foo', 'bar'],
            'mymodule': {
                'force': False,
                'extra': ['foo', 'baz'],
                'arbitrary': {
                    'nesting': {
                        'depth': 'works'
                    }
                }
            },
            'extramodule': {
                'unique': True
            }
        }

        config = LayeredConfig(Defaults(defaults))
        self.assertEquals(defaults, LayeredConfig.dump(config))


if __name__ == '__main__':
    unittest.main()
