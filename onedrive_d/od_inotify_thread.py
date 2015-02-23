#!/usr/bin/python3

import csv
import shutil
import subprocess
import threading
from time import sleep

from . import od_glob
from . import od_sqlite

class INotifyThread(threading.Thread):

	pause_event = threading.Event()

	def __init__(self, root_path, root_id, ignore_list):
		super().__init__()
		self.name = 'inotify'
		self.daemon = True
		self.running = True
		self.root_path = root_path + '/'
		self.root_id = root_id
		self.ignore_list = ignore_list
		self.logger = od_glob.get_logger()

	def stop(self):
		self.running = False

	def parse_record(self, row):

		if INotifyThread.pause_event.is_set(): return

		path, event, name = row
		
		if self.ignore_list.is_ignorable(name, path):
			# if the file / dir is in ignore list, skip it
			self.logger.debug('ignored "%s%s".', path, name)
			return
		
		parent_entry = self.entrymgr.get_entry(isdir = True, local_path = path[:-1])

		if 'CLOSE_WRITE' in event:
			# the situation is complex. cannot simply upload without knowing its remote status.
			# sync its parent without recursion
			if parent_entry != None:
				self.sync_path(path, parent_entry)
			elif path == self.root_path:
				self.sync_root()
			else:
				self.logger.info('path "%s" is not indexed.', path)
		elif 'MOVED_TO' in event:
			self.logger.debug(row)
			parent_entry_id = None
			if parent_entry == None:
				if path == self.root_path:
					parent_entry_id = self.root_id
				else:
					self.logger.info('did not find entry for dir "%s".', path)
					return
			else:
				parent_entry_id = parent_entry['remote_id']
			isdir = 'ISDIR' in event
			self.entrymgr.update_moved_entry_if_exists(isdir, path + name, parent_entry_id)
			if parent_entry != None: self.sync_path(path, parent_entry)
			else: self.sync_root()
		elif 'MOVED_FROM' in event:
			# if the OS changes mtime attribute on moving, then MOVED_TO will 
			# be reduced to an upload task.
			self.logger.debug(row)
			self.entrymgr.update_status_if_exists(isdir = 'ISDIR' in event, 
				local_path = path + name, 
				status = 'MOVED_FROM')
		elif 'DELETE' in event:
			isdir = 'ISDIR' in event
			target_entry = self.entrymgr.get_entry(isdir = isdir, 
				local_path = path + name)
			if target_entry != None:
				self.taskmgr.add_task('rm' if isdir else 'rf', 
					local_path = path + name, 
					remote_id = target_entry['remote_id'], 
					remote_parent_id = target_entry['remote_parent_id'])
			elif parent_entry != None:
				self.sync_path(path, parent_entry)
			elif path == self.root_path:
				self.sync_root()
			else:
				self.logger.info('deleted file "%s" and its parent are not indexed.', path + name)
		elif 'CREATE,ISDIR' == event:
			# some file managers produce temporary dir, so path+name is not
			# reliable. Better issue task to sync its parent, but no 
			# need to be recursive
			# For Caja file manager, creating dir results in a sequence of
			# CREATE_ISDIR, MOVE_FROM, MOVE_TO events.
			# if parent_entry == None:
			#	self.logger.info('did not find entry for dir "%s".', path)
			#	return
			#self.sync_path(path, parent_entry)
			# Not sure for other file managers.
			# Better wait until a deep sync. 
			pass

	def sync_root(self):
		self.taskmgr.add_task('sy', self.root_path[:-1], self.root_id, '')

	def sync_path(self, path, entry, args=''):
		self.taskmgr.add_task('sy', path[:-1], 
			remote_id = entry['remote_id'], 
			remote_parent_id = entry['remote_parent_id'], 
			args='')

	def run(self):
		if shutil.which('inotifywait') == None:
			# inotifywait is not installed
			self.logger.critical('`inotifywait` was not found. Skip module.')
			return

		inotify_args = ['inotifywait', '-e', 'unmount,close_write,delete,move,isdir', '-cmr', self.root_path]
		# if len(self.config.ignore_list.ignore_names) > 0:
		# 	ignore_list = []
		# 	for item in self.config.ignore_list.ignore_names:
		# 		ignore_list.append(fnmatch.translate(item).replace('\\Z(?ms)', ''))
		# 		inotify_args += ['--exclude', '(' +'|'.join(ignore_list) + ')']
		
		self.taskmgr = od_sqlite.TaskManager()
		self.entrymgr = od_sqlite.EntryManager()

		self.logger.debug('starting inotifywait process.')
		self.subp = subprocess.Popen(inotify_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while self.running:
			line = self.subp.stdout.readline().decode('utf-8').strip()
			if line == '': sleep(1)
			elif line[0] == '/':
				csv_rows = csv.reader(line.split('\n'))
				for row in csv_rows:
					self.parse_record(row)
				# del csv_rows

		self.logger.debug('exit while loop.')
		self.subp.terminate()
		subprocess.call(['kill', '-9', str(self.subp.pid)])
		self.taskmgr.close()
		self.entrymgr.close()
		self.logger.debug('stopped.')



