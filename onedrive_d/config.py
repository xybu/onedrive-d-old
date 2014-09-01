#!/usr/bin/python3

import os
import sys
import json
from calendar import timegm
from datetime import timezone, datetime, timedelta
from pwd import getpwnam
from logger import Logger

OS_HOSTNAME = os.uname()[1]
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
APP_CONFIG_LOADED = False

def now():
	return datetime.now(timezone.utc)

def time_to_str(t):
	s = t.strftime(APP_DATETIME_FORMAT)
	if '+' not in s:
		s = s + '+0000'
	return s

def str_to_time(s):
	return datetime.strptime(s, APP_DATETIME_FORMAT)

def timestamp_to_time(t):
	return datetime.fromtimestamp(t, tz=timezone.utc)

def str_to_timestamp(s):
	return timegm(str_to_time(s).timetuple())

def touch(path, data):
	'''
	Create a file and set up permission bits.
	'''
	if not os.path.isdir(os.path.dirname(path)):
		mkdir(os.path.dirname(path))
	with open(path, 'wb') as f:
		f.write(bytes(data, 'utf-8'))
	uid = getpwnam(OS_LOCAL_USER).pw_uid
	os.chown(path, uid, -1)

def mkdir(path):
	'''
	Create a path and set up owner uid.
	'''
	os.mkdir(path)
	uid = getpwnam(OS_LOCAL_USER).pw_uid
	os.chown(path, uid, -1)

def load_ignore_list():
	file_path = APP_CONFIG_PATH + '/ignore_list.txt'
	if not os.path.isfile(file_path):
		touch(file_path, '')
	f = open(file_path, 'r')
	for line in f:
		if not line.startswith('//') and line != '\n':
			APP_IGNORE_LIST.append(line.strip())
	f.close()
	return len(APP_IGNORE_LIST)

def reset_config(path = APP_CONFIG_FILE_PATH):
	touch(path, '{"log_path": null}')

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

if not APP_CONFIG_LOADED:
	if not os.path.exists(APP_CONFIG_FILE_PATH):
		try: reset_config()
		except OSError: pass
	with open(APP_CONFIG_FILE_PATH, 'r') as f:
		APP_CONFIG = json.load(f)
	
log = Logger(APP_CONFIG['log_path'], Logger.NOTSET)