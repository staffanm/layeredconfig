from __future__ import print_function

# begin import
import sys
import argparse
from datetime import date, datetime
from layeredconfig import LayeredConfig, Defaults, INIFile, Commandline
# end import


# begin defaults
defaults = Defaults({'home': str,
                     'name': 'MyApp',
                     'dostuff': bool,
                     'times': int,
                     'duedate': date,
                     'things': list,
                     'submodule': {'retry': bool,
                                   'lastrun': datetime
                               }
                     })
# end defaults

# begin inifile
with open("myapp.ini", "w") as fp:
    fp.write("""[__root__]
home = /tmp/myapp
dostuff = False
times = 4
duedate = 2014-10-30
things = Huey, Dewey, Louie

[submodule]
retry = False
lastrun = 2014-10-30 16:40:22
""")
inifile = INIFile("myapp.ini")
# end inifile

# begin argparse
parser = argparse.ArgumentParser("This is a simple program")
parser.add_argument("--home", help="The home directory of the app")
parser.add_argument('--dostuff', action="store_true", help="Do some work")
parser.add_argument("-t", "--times", type=int, help="Number of times to do it")
parser.add_argument('--things', action="append", help="Extra things to crunch")
parser.add_argument('--retry', action="store_true", help="Try again")
parser.add_argument("file", metavar="FILE", help="The filename to process")
# end argparse

# begin layeredconfig
sys.argv = ['./myapp.py', '--home=/opt/myapp', '-t=2', '--dostuff', 'file.txt']
cfg = LayeredConfig(defaults,
                    inifile,
                    Commandline(parser=parser))
print("Starting %s in %s for %r times (doing work: %s)" % (cfg.name,
                                                           cfg.home,
                                                           cfg.times,
                                                           cfg.dostuff))
# should print "Starting MyApp in /opt/myapp for 2 times (doing work: True)"
# end layeredconfig

# begin showhelp
# also, running your program with -h works
sys.argv = ['./myapp.py', '-h']
cfg = LayeredConfig(defaults,
                    inifile,
                    Commandline(parser=parser))
# end showhelp

# begin nodefaults

# NOTE: we never reach this because the previous call to -h will have
# called sys.exit

cfg = LayeredConfig(inifile,
                    Commandline(parser=parser))
# note that cfg.times is now a str, not an int
print("Starting in %s for %r times" % (cfg.home, cfg.times))
# end nodefaults
