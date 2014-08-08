#!/usr/bin/python3

import os
import sys
import json
from datetime import timezone, datetime, timedelta
from pwd import getpwnam
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
APP_IGNORE_LIST = []
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

def touch(path, data):
	'''
	Create a file and set up permission bits.
	'''
	if not os.path.isdir(os.path.dirname(path)):
		mkdir(os.path.dirname(path))
	with open(path, 'w') as f:
		f.write(data)
	uid = getpwnam(OS_LOCAL_USER).pw_uid
	os.chown(path, uid, -1)

def mkdir(path):
	'''
	Create a path and set up owner uid.
	'''
	os.mkdir(path)
	uid = getpwnam(OS_LOCAL_USER).pw_uid
	os.chown(path, uid, -1)

def load_config(path = APP_CONFIG_FILE_PATH):
	with open(path, 'r') as f:
		global APP_CONFIG
		APP_CONFIG = json.load(f)

def load_ignore_list():
	file_path = APP_CONFIG_PATH + '/ignore_list.txt'
	if not os.path.isfile(file_path):
		touch(file_path, '')
	with open(file_path, 'r') as f:
		APP_IGNORE_LIST = f.readlines()
	return len(APP_IGNORE_LIST)

def save_ignore_list():
	with open(APP_CONFIG_PATH + '/ignore_list.txt', 'w') as f:
		f.write('\n'.join(APP_IGNORE_LIST))

def reset_config(path = APP_CONFIG_FILE_PATH):
	touch(path, '{}')

def set_config(name, value):
	APP_CONFIG[name] = value

def unset_config(name):
	if name in APP_CONFIG: del APP_CONFIG[name]

def test_base_path():
	if 'base_path' not in APP_CONFIG: return False
	else: return os.path.isdir(APP_CONFIG['base_path'])

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