"""
Account database abstraction. It solves the OS user and loads the account info
associated with the OS user.
"""

import os
import sys
import pwd

from . import od_bootstrap


ACCOUNT_INVENTORY = '/etc/onedrived'


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


def get_user_config(user_info, terminate=False):
	if not os.path.isfile(ACCOUNT_INVENTORY + '/' + str(user_info['os_user_uid']) + '.db'):
		if terminate:
			die('User "{0}" ({1}) has not configured onedrive-d (003).'.format(user_info['os_user_name'], user_info['os_user_uid']))
		else:
			return None
	# TODO: load information from database
	return None


def drop_root_privilege(user_info):
	try:
		# must drop group privilege before user privilege
		os.setgid(user_info['os_user_gid'])
		os.setuid(user_info['os_user_uid'])
	except OSError as e:
		die('Failed to drop root privilege - {0} (004.{1}).'.format(e.strerror, e.errno))
