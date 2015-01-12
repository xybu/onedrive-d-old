#!/usr/bin/python3

'''
Global variables for onedrive_d.
'''

import os
import sys
import logging
import atexit
import json
from calendar import timegm
from datetime import timezone, datetime, timedelta
from pwd import getpwnam
import od_ignore_list

config_instance = None
logger_instance = None

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
APP_CLIENT_ID = '000000004010C916'
APP_CLIENT_SECRET = 'PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi'
APP_VERSION = '1.0-dev'

def get_config_instance(force = False, setup_mode = False):
	global config_instance
	# callingframe = sys._getframe(1)
	# print('My caller is the %r function in a %r class' % (
	# 	callingframe.f_code.co_name, 
	# 	callingframe.f_locals['self'].__class__.__name__))
	if force or config_instance == None: 
		config_instance = ConfigSet(setup_mode)
		atexit.register(dump_config)
	return config_instance

def get_logger():
	global logger_instance
	if logger_instance == None:
		logging.basicConfig(format = '[%(asctime)-15s] %(threadName)s: %(message)s')
		logger_instance = logging.getLogger(__name__)
		logger_instance.setLevel(logging.DEBUG)
	return logger_instance

def now():
	return datetime.now(timezone.utc)

def time_to_str(t):
	s = t.strftime(DATETIME_FORMAT)
	if '+' not in s: s = s + '+0000'
	return s

def str_to_time(s):
	return datetime.strptime(s, DATETIME_FORMAT)

def str_to_timestamp(s):
	return timegm(str_to_time(s).timetuple())

def mkdir(path, uid):
	'''
	Create a path and set up owner uid.
	'''
	os.mkdir(path)
	os.chown(path, uid, -1)

def dump_config():
	if config_instance != None and config_instance.is_dirty:
		config_instance.dump()

class ConfigSet:

	params = {
		'NETWORK_ERROR_RETRY_INTERVAL': 10, # in seconds
		'ONEDRIVE_ROOT_PATH': None,
		'ONEDRIVE_TOKENS': None,
		'ONEDRIVE_TOKENS_EXP': None
	}
	
	def __init__(self, setup_mode = False):
		
		self.is_dirty = False
		self.OS_HOSTNAME = os.uname()[1]
		self.OS_USERNAME = os.getenv('SUDO_USER')
		if self.OS_USERNAME == None or self.OS_USERNAME == '':
			self.OS_USERNAME = os.getenv('USER')
		if self.OS_USERNAME == None or self.OS_USERNAME == '':
			get_logger().critical('cannot find current logged-in user.')
			sys.exit(1)
		
		self.OS_USER_ID = getpwnam(self.OS_USERNAME).pw_uid
		self.OS_HOME_PATH = os.path.expanduser('~' + self.OS_USERNAME)
		self.APP_CONF_PATH = self.OS_HOME_PATH + '/.onedrive'
		
		if not os.path.exists(self.APP_CONF_PATH):
			get_logger().critical('onedrive-d may not be installed properly. Exit.')
			sys.exit(1)
		
		self.APP_CONF_FILE = self.APP_CONF_PATH + '/config_v2.json'
		
		if os.path.exists(self.APP_CONF_FILE):
			try:
				with open(self.APP_CONF_FILE, 'r') as f:
					saved_params = json.loads(f.read())
					for key in saved_params:
						ConfigSet.params[key] = saved_params[key]
			except:
				get_logger().info('fail to read config file "' + self.APP_CONF_FILE + '". Use default.')
		elif not setup_mode:
				get_logger().critical('onedrive-d config file does not exist. Exit.')
				sys.exit(1)
		
		if ConfigSet.params['ONEDRIVE_ROOT_PATH'] == None and not setup_mode:
			get_logger().critical('path to local OneDrive repo is not set.')
			sys.exit(1)
		
		self.APP_IGNORE_FILE = self.APP_CONF_PATH + '/ignore_v2.ini'
		
		if not setup_mode:
			if os.path.exists(self.APP_IGNORE_FILE):
				self.ignore_list = od_ignore_list.IgnoreList(self.APP_IGNORE_FILE, ConfigSet.params['ONEDRIVE_ROOT_PATH'])
			else: 
				get_logger().info('ignore list file was not found.')
				self.ignore_list = None
	
	def set_root_path(self, path):
		ConfigSet.params['ONEDRIVE_ROOT_PATH'] = path
		self.is_dirty = True
	
	def get_access_token(self):
		if ConfigSet.params['ONEDRIVE_TOKENS'] != None:
			if str_to_time(ConfigSet.params['ONEDRIVE_TOKENS_EXP']) < now(): return None
		return ConfigSet.params['ONEDRIVE_TOKENS']
	
	def set_access_token(self, tokens):
		d = now() + timedelta(seconds = tokens['expires_in'])
		ConfigSet.params['ONEDRIVE_TOKENS'] = tokens
		ConfigSet.params['ONEDRIVE_TOKENS_EXP'] = time_to_str(d)
		self.is_dirty = True
	
	def dump(self):
		try:
			with open(self.APP_CONF_FILE, 'w') as f:
				json.dump(ConfigSet.params, f)
			os.chown(self.APP_CONF_FILE, self.OS_USER_ID, -1)
			get_logger().info('config saved.')
		except:
			get_logger().info('failed to dump config to file "' + self.APP_CONF_FILE + '".')
	