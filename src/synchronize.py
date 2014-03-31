#!/usr/bin/env python

# synchronize.py
# 
# The upper-level driver of python-skydrive
# @author	Xiangyu Bu
# @date		Jan 07, 2013

import sys, os
import yaml
from entries import * 

settingsFile = open(os.path.expanduser("~/.onedrive/user.conf"), "r")
settingsMap = yaml.safe_load(settingsFile)
settingsFile.close()

ONEDRIVE_ROOT_DIR = settingsMap["rootPath"] + "/"

rootEntry = DirectoryEntry(ONEDRIVE_ROOT_DIR, "", "")
rootEntry.sync()
