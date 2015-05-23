"""
Global functions and configurations.
"""

import os
import logging
import atexit


Log = None


def get_logger(level=logging.DEBUG, file_path=None):
	global Log
	if Log is None:
		logging.basicConfig(format='[%(asctime)-15s] %(levelname)s: %(threadName)s: %(message)s')
		Log = logging.getLogger(__name__)
		Log.setLevel(level)
		if file_path is not None:
			Log.propagate = False
			logger_fh = logging.FileHandler(file_path, 'a')
			logger_fh.setLevel(level)
			Log.addHandler(logger_fh)
		atexit.register(shutdown_log_atexit)
	return Log


def shutdown_log_atexit():
	global Log
	if Log is not None:
		logging.shutdown()


def mkdir(path, uid, gid = -1):
	"""Create a path and set up owner uid."""
	os.mkdir(path)
	os.chown(path, uid, gid)
