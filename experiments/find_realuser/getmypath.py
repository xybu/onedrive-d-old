#!/usr/bin/python

import os

HOME_PATH = os.path.expanduser("~")
LOCAL_USER = os.getenv("SUDO_USER")
if LOCAL_USER == None or LOCAL_USER == "":
	# the user isn't running sudo
	LOCAL_USER = os.getenv("USER")
else:
	# when in SUDO, fix the HOME_PATH
	# may not be necessary on most OSes
	# buggy!!
	HOME_PATH = os.path.expanduser("~" + LOCAL_USER)

print "The actual user is " + LOCAL_USER
print "The actual home dir is " + HOME_PATH
