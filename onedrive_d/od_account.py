"""
Account database abstraction. It solves the OS user and loads the account info
associated with the OS user.
"""

import os
import sys
import pwd
import configparser

from . import od_bootstrap
from . import od_accountdb


USER_CONFIG_FILE_PATH = '.onedrive/settings_v1.ini'


def die(msg):
	od_bootstrap.get_logger().critical(msg)
	sys.exit(1)


def get_user_info():
	"""Resolve the OS user and return the username, uid, gid, and home dir."""
	# check root permission
	if os.geteuid() != 0:
		die('onedrive-d daemon must run as root (001).')
	# resolve real user
	real_uid = int(os.getenv('SUDO_UID', 0))
	if real_uid == 0:
		die('onedrive-d daemon cannot find the real login user (002).')
	user_info = pwd.getpwuid(real_uid)
	return {
		'os_user_uid': real_uid,
		'os_user_gid': user_info.pw_gid,
		'os_user_name': user_info.pw_name,
		'os_user_home': user_info.pw_dir,
	}


def get_default_config_dict():
	return {
		'Intervals': {
			'NETWORK_RETRY_INTERVAL': 20
		}
	}


def get_default_config():
	ret = configparser.ConfigParser()
	ret.read_dict(get_default_config_dict())
	return ret


def get_user_account(user_info, terminate=False):
	if not os.path.isfile(od_accountdb.get_accountdb_path(str(user_info['os_user_uid']))):
		if terminate:
			die('User "{0}" ({1}) has not configured onedrive-d (003).'.format(user_info['os_user_name'], user_info['os_user_uid']))
	return None	


def get_user_config(user_info, terminate=False):
	config_file_path = user_info['os_user_home'] + '/' + USER_CONFIG_FILE_PATH
	if not os.path.isfile(config_file_path):
		if terminate:
			die('User "{0}" ({1}) has not configured onedrive-d (003).'.format(user_info['os_user_name'], user_info['os_user_uid']))
		return None
	config = configparser.ConfigParser()
	with open(config_file_path, 'r') as f:
		config.read_file(f)
	# sanitize the existing config file
	default_dict = get_default_config_dict()
	for section_name in default_dict:
		if not config.has_section(section_name):
			config.add_section(section_name)
		for k in default_dict[section_name]:
			if not config.has_option(section_name, k):
				config.set(section_name, k, str(default_dict[section_name][k]))
	return config


def drop_root_privilege(user_info):
	try:
		# must drop group privilege before user privilege
		os.setgid(user_info['os_user_gid'])
		os.setuid(user_info['os_user_uid'])
	except OSError as e:
		die('Failed to drop root privilege - {0} (004.{1}).'.format(e.strerror, e.errno))



