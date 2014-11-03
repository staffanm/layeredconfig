from __future__ import print_function
# begin firststep
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
# end firststep

return_value = True
