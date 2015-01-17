#!/usr/bin/python3

import os
import sys
import threading
import od_glob
import od_onedrive_api
import od_inotify_thread
import od_scanner_thread
import od_worker_thread

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
	
	def test_quota(self):
		self.logger.info('try getting quota info.')
		print(self.api.get_quota())
	
	def start(self):
		try:
			self.logger.info('daemon started.')
			self.load_token()
			self.test_quota()
		except KeyboardInterrupt:
			sys.exit(0)