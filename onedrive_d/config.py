#!/usr/bin/python3

import os
import sys
import json
from datetime import timezone, datetime, timedelta
import logger

OS_LOCAL_USER = os.getenv('SUDO_USER')
if OS_LOCAL_USER == None or OS_LOCAL_USER == '':
	OS_LOCAL_USER = os.getenv('USER')

if OS_LOCAL_USER == None:
	print('Error: cannot get the system username.')
	sys.exit(1)

USER_HOME_PATH = os.path.expanduser('~' + OS_LOCAL_USER)

APP_CONFIG_PATH = USER_HOME_PATH + '/.onedrive'
APP_CONFIG_FILE_PATH = APP_CONFIG_PATH + '/config.json'
APP_CONFIG = {}
APP_CLIENT_ID = '000000004010C916'
APP_CLIENT_SECRET = 'PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi'
APP_VERSION = '1.0-dev'
APP_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

LOGGING_FILE_PATH = None
LOGGING_MIN_LEVEL = logger.Logger.NOTSET

def now():
	return datetime.now(timezone.utc)

def time_to_str(t):
	s = t.strftime(APP_DATETIME_FORMAT)
	if '+' not in s:
		s = s + '+0000'
	return s

def str_to_time(s):
	return datetime.strptime(s, APP_DATETIME_FORMAT)

def reset_config(path = APP_CONFIG_FILE_PATH):
	if not os.path.isdir(os.path.dirname(path)):
		os.mkdir(os.path.dirname(path))
	with open(path, 'w') as f:
		f.write('{}')
	import pwd
	uid = pwd.getpwnam(OS_LOCAL_USER).pw_uid
	os.chown(path, uid, -1)

def load_config(path = APP_CONFIG_FILE_PATH):
	with open(path, 'r') as f:
		global APP_CONFIG
		APP_CONFIG = json.load(f)

def set_config(name, value):
	APP_CONFIG[name] = value

def unset_config(name):
	del APP_CONFIG[name]

def has_token():
	return 'token' in APP_CONFIG

def get_token():
	if not has_token(): return None
	token_exp = str_to_time(APP_CONFIG['token_expiration'])
	if now() > token_exp: return None
	else: return APP_CONFIG['token']

def save_token(tokens):
	d = timedelta(seconds = tokens['expires_in'])
	e = now() + d
	set_config('token_expiration', time_to_str(e))
	set_config('token', tokens)

def save_config(path = APP_CONFIG_FILE_PATH):
	assert len(APP_CONFIG) > 0, 'The configuration dict is not loaded.'
	with open(path, 'w') as f:
		json.dump(APP_CONFIG, f)