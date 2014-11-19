# begin import-1
from __future__ import print_function
from layeredconfig import LayeredConfig
# end import-1

# begin import-2
from layeredconfig import Defaults, INIFile, Environment, Commandline
# end import-2

# begin defaults
from datetime import date, datetime
mydefaults = Defaults({'home': '/tmp/myapp',
                       'name': 'MyApp',
                       'dostuff': False,
                       'times': 4,
                       'duedate': date(2014, 10, 30),
                       'things': ['Huey', 'Dewey', 'Louie'],
                       'submodule': {
                           'retry': False,
                           'lastrun': datetime(2014, 10, 30, 16, 40, 22)
                           }
                       })
# end defaults

# begin inifile
myinifile = INIFile("myapp.ini")
# end inifile

# begin environment
env = {'MYAPP_HOME': 'C:\\Progra~1\\MyApp',
       'MYAPP_SUBMODULE_RETRY': 'True'}
myenv = Environment(env, prefix="MYAPP_")
# end environment

# begin commandline
mycmdline = Commandline(['-f', '--home=/opt/myapp', '--times=2', '--dostuff'])
rest = mycmdline.rest
# end commandline
assert rest == ['-f']

# begin makeconfig
cfg = LayeredConfig(mydefaults,
                    myinifile,
                    myenv,
                    mycmdline)
# end makeconfig
import os
def do_stuff(action, idx):
    pass

# begin useconfig
print("%s starting, home in %s" % (cfg.name, cfg.home))
# end useconfig

# begin usetyping
delay = date.today() - cfg.duedate  # date
if cfg.dostuff: # bool
    for i in range(cfg.times):  # int
        print(", ".join(cfg.things))  # list
# end usetyping

# begin usesubconfig
subcfg = cfg.submodule  
if subcfg.retry:
    print(subcfg.lastrun.isoformat())
# end usesubconfig

try:
    print(subcfg.home)
except AttributeError:
    pass

# begin usecascade
cfg = LayeredConfig(mydefaults, myinifile, myenv, mycmdline, cascade=True)
subcfg = cfg.submodule
print(subcfg.home)  # prints '/opt/myapp', from Commandline source root section
# end usecascade
assert subcfg.home == '/opt/myapp'

# begin writeconfig
subcfg.lastrun = datetime.now()
LayeredConfig.write(cfg)
# end writeconfig

return_value = True
