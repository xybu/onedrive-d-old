#!/usr/bin/python3

import os
import gc
import sys
import time
import signal
import atexit
import threading
from . import od_glob
from . import od_onedrive_api
from . import od_sqlite
from . import od_inotify_thread
from . import od_worker_thread


class Monitor:

	def __init__(self):
		self.logger = od_glob.get_logger()
		self.config = od_glob.get_config_instance()
		self.api = od_onedrive_api.get_instance()
		self.taskmgr = None
		self.entrymgr = None
		self.inotify_thread = None
		atexit.register(self.cleanup)
		signal.signal(signal.SIGTERM, self.stop)

	def load_token(self):
		tokens = self.config.get_access_token()
		if tokens is None:
			self.logger.critical('no user is associated with onedrive-d.')
			sys.exit(1)
		elif self.config.is_token_expired():
			self.logger.info('token has expired. Try refreshing it.')
			self.api.set_refresh_token(tokens['refresh_token'])
			try:
				self.api.auto_recover_auth_error()
				self.logger.info('successfully refreshed access token.')
			except Exception as e:
				self.logger.critical(e)
				sys.exit(1)
		else:
			# the token exists and is not expired
			self.api.set_access_token(tokens['access_token'])
			self.api.set_refresh_token(tokens['refresh_token'])
			self.api.set_user_id(tokens['user_id'])
		self.root_entry_id = self.api.get_property()['id']
		self.api.ROOT_ENTRY_ID = self.root_entry_id

	def test_quota(self):
		self.logger.info('try getting quota info.')
		print(self.api.get_quota())

	def create_workers(self):
		self.taskmgr = od_sqlite.TaskManager()
		for i in range(0, self.config.params['NUM_OF_WORKERS']):
			od_worker_thread.WorkerThread().start()

	def create_inotify_thread(self):
		od_inotify_thread.INotifyThread.pause_event.clear()
		self.inotify_thread = od_inotify_thread.INotifyThread(
			root_path=self.config.params['ONEDRIVE_ROOT_PATH'],
			root_id=self.root_entry_id,
			ignore_list=self.config.ignore_list)
		self.inotify_thread.start()

	def heart_beat(self):
		self.entrymgr = od_sqlite.EntryManager()
		while True:
			# self.taskmgr.add_task(**{
			# 	'type': 'sy',
			# 	'local_path': self.config.params['ONEDRIVE_ROOT_PATH'],
			# 	'remote_id': root_entry_id,
			# 	'args': 'recursive,'
			# })
			self.taskmgr.add_task('sy',
				local_path=self.config.params['ONEDRIVE_ROOT_PATH'],
				remote_id=self.root_entry_id,
				args='recursive,')
			time.sleep(self.config.params['DEEP_SCAN_INTERVAL'])
			gc.collect()

	def cleanup(self):
		self.logger.debug('cleaning up.')
		if self.entrymgr is not None:
			self.entrymgr.del_unvisited_entries()
			self.entrymgr.close()
			self.logger.debug('entry manager closed.')
		if self.inotify_thread is not None:
			self.inotify_thread.stop()
			self.inotify_thread.join()
			self.logger.debug('inotify thread stopped.')
		if self.taskmgr is not None:
			self.taskmgr.clean_tasks()
			self.logger.debug('task queue cleaned.')
			od_worker_thread.WorkerThread.worker_lock.acquire()
			for w in od_worker_thread.WorkerThread.worker_list:
				w.stop()
			for w in od_worker_thread.WorkerThread.worker_list:
				self.taskmgr.inc_sem()
			for w in od_worker_thread.WorkerThread.worker_list:
				self.logger.debug('waiting for thread %s.', w.name)
				w.join()
			od_worker_thread.WorkerThread.worker_lock.release()
			self.taskmgr.close()

	def start(self):
		gc.enable()
		self.logger.debug('daemon started.')
		# do not check root path because it is checked in config
		self.load_token()
		# self.test_quota()
		od_glob.will_update_last_run_time()
		self.create_workers()
		self.create_inotify_thread()
		self.heart_beat()

	def stop(self, sig_num=None, stack_frame=None):
		self.logger.info('stopping...')
		sys.exit(0)
