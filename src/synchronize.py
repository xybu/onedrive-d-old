#!/usr/bin/env python

# synchronize.py
# 
# The upper-level driver of python-skydrive
# @author	Xiangyu Bu
# @date		Jan 07, 2013

import sys, os
import yaml
import entries

settingsFile = open(os.path.expanduser("~/.skydrive/user.conf"), "r");
settingsMap = yaml.safe_load(settingsFile)
settingsFile.close()

SKYDRIVE_ROOT_DIR = settingsMap["rootPath"] + "/"

rootEntry = DirectoryEntry(SKYDRIVE_ROOT_DIR, "", "")
rootEntry.sync()
