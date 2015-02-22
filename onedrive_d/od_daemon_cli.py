#!/usr/bin/python3

import os
import sys
import time
import threading
from . import od_glob
from . import od_onedrive_api
from . import od_sqlite
from . import od_inotify_thread
from . import od_worker_thread

class Daemon:
	
	def __init__(self):
		self.logger = od_glob.get_logger()
		self.config = od_glob.get_config_instance()
		self.api = od_onedrive_api.get_instance()
	
	def load_token(self):
		tokens = self.config.get_access_token()
		if tokens == None:
			self.logger.critical('no user is associated with onedrive-d.')
			sys.exit(1)
		elif self.config.is_token_expired():
			self.logger.info('token has expired. Try refreshing it.')
			self.api.set_refresh_token(tokens['refresh_token'])
			try:
				self.api.auto_recover_auth_error()
				self.logger.info('successfully refreshed access token.')
			except Exception as e:
				self.logger.critical('an unknown error occurred. {}' % e)
				sys.exit(1)
		else:
			# the token exists and is not expired
			self.api.set_access_token(tokens['access_token'])
			self.api.set_refresh_token(tokens['refresh_token'])
			self.api.set_user_id(tokens['user_id'])
	
	def test_quota(self):
		self.logger.info('try getting quota info.')
		print(self.api.get_quota())
	
	def create_workers(self):
		for i in range (0, self.config.params['NUM_OF_WORKERS']):
			od_worker_thread.WorkerThread().start()
	
	def heart_beat(self):
		self.taskmgr = od_sqlite.TaskManager()
		while True:
			self.taskmgr.add_task(**{
				'type': 'sy',
				'local_path': self.config.params['ONEDRIVE_ROOT_PATH'], 
				'remote_id': self.api.get_root_entry_name()
			})
			time.sleep(self.config.params['DEEP_SCAN_INTERVAL'])
	
	def start(self):
		try:
			self.logger.info('daemon started.')
			# do not check root path because it is checked in config
			self.load_token()
			self.test_quota()
			self.create_workers()
			self.heart_beat()
		except KeyboardInterrupt:
			# for debugging, dump task db
			# print('SQLite TaskManager Dump:')
			# for line in self.taskmgr.dump():
			# 	print(line)
			sys.exit(0)