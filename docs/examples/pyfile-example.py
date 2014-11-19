# begin example
from layeredconfig import LayeredConfig, PyFile, Defaults
from datetime import date, datetime

conf = LayeredConfig(Defaults({'home': '/tmp/myapp',
                               'name': 'MyApp',
                               'dostuff': False,
                               'times': 4,
                               'duedate': date(2014, 10, 30),
                               'things': ['Huey', 'Dewey', 'Louie'],
                               'submodule': {
                                   'retry': False,
                                   'lastrun': datetime(2014, 10, 30, 16, 40, 22)
                               }
                           }),
                     PyFile("conf.py"))
# end example
from datetime import date, datetime
import os
assert conf.home == os.getcwd()
assert conf.name == 'My App'
assert conf.dostuff is True
assert conf.times == 4
assert conf.duedate == date.today()
assert conf.things == ['Huey', 'Dewey', 'Louie']
assert conf.submodule.lastrun == datetime(2014, 10, 30, 16, 40, 22)
assert conf.submodule.retry is True

return_value = conf.name
