#!/usr/bin/python3

import os
import sys
import json
import logger

OS_LOCAL_USER = os.getenv('SUDO_USER')
if OS_LOCAL_USER == None or OS_LOCAL_USER == '':
	OS_LOCAL_USER = os.getenv('USER')

if OS_LOCAL_USER == None:
	print('Error: cannot get the system username.')
	sys.exit(1)

USER_HOME_PATH = os.path.expanduser('~' + OS_LOCAL_USER)

APP_CONFIG_PATH = USER_HOME_PATH + '/.onedrive'

APP_CREDENTIALS = {
	'client_id': '000000004010C916', 
	'client_secret': 'PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi'
}

APP_VERSION = '1.0-dev'
