#!/usr/bin/python3

"""
Global variables for onedrive_d.
"""

import os
import sys
import logging
import atexit
import json
from calendar import timegm
from datetime import timezone, datetime, timedelta
from pwd import getpwnam
from . import od_ignore_list

config_instance = None
logger_instance = None
update_last_run_timestamp = False

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
APP_CLIENT_ID = '000000004010C916'
APP_CLIENT_SECRET = 'PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi'
APP_VERSION = '1.1.0dev'


def get_config_instance(force=False, setup_mode=False):
	global config_instance
	# callingframe = sys._getframe(1)
	# print('My caller is the %r function in a %r class' % (
	# 	callingframe.f_code.co_name,
	# 	callingframe.f_locals['self'].__class__.__name__))
	if force or config_instance is None:
		config_instance = ConfigSet(setup_mode)
		atexit.register(dump_config)
	return config_instance


def get_logger(level=logging.DEBUG, file_path=None):
	global logger_instance
	if logger_instance is None:
		logging.basicConfig(format='[%(asctime)-15s] %(levelname)s: %(threadName)s: %(message)s')
		logger_instance = logging.getLogger(__name__)
		logger_instance.setLevel(level)
		if file_path is not None:
			logger_instance.propagate = False
			logger_fh = logging.WatchedFileHandler(file_path, 'a')
			logger_fh.setLevel(level)
			logger_instance.addHandler(logger_fh)
		atexit.register(flush_log_at_shutdown)
	return logger_instance


def now():
	return datetime.now(timezone.utc)


def time_to_str(t):
	s = t.strftime(DATETIME_FORMAT)
	if '+' not in s:
		s = s + '+0000'
	return s


def str_to_time(s):
	return datetime.strptime(s, DATETIME_FORMAT)


def str_to_timestamp(s):
	return timegm(str_to_time(s).timetuple())


def timestamp_to_time(t):
	return datetime.fromtimestamp(t, tz=timezone.utc)


def mkdir(path, uid):
	"""
	Create a path and set up owner uid.
	"""
	os.mkdir(path)
	os.chown(path, uid, -1)


def flush_log_at_shutdown():
	global logger_instance
	if logger_instance is not None:
		logging.shutdown()


def will_update_last_run_time():
	update_last_run_timestamp = True


def dump_config():
	if update_last_run_timestamp and config_instance is not None:
		config_instance.set_last_run_timestamp()
	if config_instance is not None and ConfigSet.is_dirty:
		config_instance.dump()


class ConfigSet:

	params = {
		'NETWORK_ERROR_RETRY_INTERVAL': 10,  # in seconds
		'DEEP_SCAN_INTERVAL': 60,  # in seconds
		'NUM_OF_WORKERS': 4,
		# files > 4 MiB will be uploaded with BITS API
		'BITS_FILE_MIN_SIZE': 4194304,
		# 512 KiB per block for BITS API
		'BITS_BLOCK_SIZE': 524288,
		'ONEDRIVE_ROOT_PATH': None,
		'ONEDRIVE_TOKENS': None,
		'ONEDRIVE_TOKENS_EXP': None,
		'USE_GUI': False,
		'MIN_LOG_LEVEL': logging.DEBUG,
		'LOG_FILE_PATH': '/var/log/onedrive_d.log',
		'LAST_RUN_TIMESTAMP': '1970-01-01T00:00:00+0000'
	}

	OS_HOSTNAME = os.uname()[1]
	OS_USERNAME = os.getenv('SUDO_USER')

	initialized = False
	is_dirty = False

	def __init__(self, setup_mode=False):
		# no locking is necessary because the code is run way before multithreading
		if not ConfigSet.initialized:
			if ConfigSet.OS_USERNAME is None or ConfigSet.OS_USERNAME == '':
				ConfigSet.OS_USERNAME = os.getenv('USER')
			if ConfigSet.OS_USERNAME is None or ConfigSet.OS_USERNAME == '':
				get_logger().critical('cannot find current logged-in user.')
				sys.exit(1)
			ConfigSet.OS_USER_ID = getpwnam(ConfigSet.OS_USERNAME).pw_uid
			ConfigSet.OS_HOME_PATH = os.path.expanduser('~' + ConfigSet.OS_USERNAME)
			ConfigSet.APP_CONF_PATH = ConfigSet.OS_HOME_PATH + '/.onedrive'
			if not os.path.exists(ConfigSet.APP_CONF_PATH):
				get_logger().critical('onedrive-d may not be installed properly. Exit.')
				sys.exit(1)
			ConfigSet.APP_CONF_FILE = ConfigSet.APP_CONF_PATH + '/config_v2.json'
			if os.path.exists(ConfigSet.APP_CONF_FILE):
				try:
					with open(ConfigSet.APP_CONF_FILE, 'r') as f:
						saved_params = json.loads(f.read())
						for key in saved_params:
							ConfigSet.params[key] = saved_params[key]
				except:
					get_logger().info(
						'fail to read config file "' + ConfigSet.APP_CONF_FILE + '". Use default.')
			elif not setup_mode:
				get_logger().critical('onedrive-d config file does not exist. Exit.')
				sys.exit(1)
			if ConfigSet.params['ONEDRIVE_ROOT_PATH'] is None and not setup_mode:
				get_logger().critical('path to local OneDrive repo is not set.')
				sys.exit(1)
			ConfigSet.LAST_RUN_TIMESTAMP = str_to_time(ConfigSet.params['LAST_RUN_TIMESTAMP'])
			ConfigSet.APP_IGNORE_FILE = ConfigSet.APP_CONF_PATH + '/ignore_v2.ini'
			ConfigSet.initialized = True
			print('Loading configuration ... OK')

		if not setup_mode:
			if os.path.exists(ConfigSet.APP_IGNORE_FILE):
				self.ignore_list = od_ignore_list.IgnoreList(
					ConfigSet.APP_IGNORE_FILE, ConfigSet.params['ONEDRIVE_ROOT_PATH'])
			else:
				get_logger().info('ignore list file was not found.')
				ConfigSet.ignore_list = None

	def set_root_path(self, path):
		ConfigSet.params['ONEDRIVE_ROOT_PATH'] = path
		ConfigSet.is_dirty = True

	def set_last_run_timestamp(self):
		ConfigSet.params['LAST_RUN_TIMESTAMP'] = time_to_str(now())
		ConfigSet.is_dirty = True

	def get_access_token(self):
		if ConfigSet.params['ONEDRIVE_TOKENS'] is not None:
			return ConfigSet.params['ONEDRIVE_TOKENS']
		else:
			return None

	def is_token_expired(self):
		return str_to_time(ConfigSet.params['ONEDRIVE_TOKENS_EXP']) < now()

	def set_access_token(self, tokens):
		d = now() + timedelta(seconds=tokens['expires_in'])
		ConfigSet.params['ONEDRIVE_TOKENS'] = tokens
		ConfigSet.params['ONEDRIVE_TOKENS_EXP'] = time_to_str(d)
		ConfigSet.is_dirty = True

	def dump(self):
		try:
			with open(ConfigSet.APP_CONF_FILE, 'w') as f:
				json.dump(ConfigSet.params, f)
			os.chown(ConfigSet.APP_CONF_FILE, ConfigSet.OS_USER_ID, -1)
			get_logger().debug('config saved.')
		except:
			get_logger().warning(
				'failed to dump config to file "' + ConfigSet.APP_CONF_FILE + '".')
