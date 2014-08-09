#!/usr/bin/python3

import os
import io
import sys
import csv
import time
import json
import queue
import threading
import subprocess
import fnmatch
import config
import logger

daemon_logger = logger.Logger(None, config.LOGGING_MIN_LEVEL)

def is_ignorable(name):
	for pattern in config.APP_IGNORE_LIST:
		if fnmatch.fnmatch(name, pattern): return True
	return False

class OneDrive_INotifyThread(threading.Thread):
	def __init__(self, parent):
		super().__init__()
		self.name = 'inotify'
		self.daemon = True
		self.parent = parent
		self.is_running = False
		if len(config.APP_IGNORE_LIST) == 0:
			daemon_logger.info('ignore list is empty.')
			self.exclusion_args = []
		else:
			ignore_list = []
			for item in config.APP_IGNORE_LIST:
				ignore_list.append(fnmatch.translate(item).replace('\\Z(?ms)', ''))
			self.exclusion_args = ['--exclude', '(' +'|'.join(ignore_list) + ')']
	
	def shut_down(self):
		self.is_running = False
	
	def run(self):
		daemon_logger.info('start running.')
		self.is_running = True
		subp = subprocess.Popen(['inotifywait', '-e', 'unmount,close_write,delete,move,isdir', '-cmr', config.APP_CONFIG['base_path']] + self.exclusion_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while self.is_running:
			line = subp.stdout.readline().decode('utf-8')
			if line == '': time.sleep(1)
			elif line[0] == '/':
				line = line.rstrip()
				csv_rows = csv.reader(io.StringIO(line))
				for row in csv_rows:
					self.parent.on_inotify_task_created(row)
		subp.terminate()
		subprocess.call(['kill', '-9', str(subp.pid)])
		daemon_logger.info('inotify shut down.')

class OneDrive_Synchronizer:
	
	def __init__(self, api):
		self.api = api
		self.running = False
		self.queue = queue.Queue()
	
	def enqueue(self, local_path, remote_path):
		self.queue.put((local_path, remote_path))
	
	def is_busy(self):
		return self.running
	
	def get_file(self, local_path, remote_path):
		pass
	
	def put_file(self, local_path, remote_path):
		pass
	
	def move_file(self, remote_from, remote_to):
		pass
	
	def copy_file(self, remote_from, remote_to):
		pass
	
	def mkdir(self, remote_path):
		pass
	
	def resolve_case_conflict(self, path):
		'''
		Rename files with case conflicts
		and return the file list of the path
		'''
		ent_count = {}
		ent_list = []
		entris = os.listdir(path)
		path = path + '/'
		for ent in entris:
			ent_lower = ent.lower()
			if ent_lower in ent_count:
				# case conflict
				ent_count[ent_lower] =  1
				file_name = os.path.splitext(ent)
				ent_new = file_name[0] + ' (case_conflict_' + str(ent_count[ent_lower]) + ')' + file_name[1]
				os.rename(path + ent, path + ent_new)
				ent = ent_new
			else:
				ent_count[ent_lower] = 0
			ent_list.append(ent)
		del ent_count
		return ent_list
	
	def merge_dir(self, entry):
		'''
		A remote-first dir merge mechanism.
		'''
		local_path, remote_path = entry
		
		all_remote_items = self.api.list_entries(remote_path)
		all_local_items = self.resolve_case_conflict(local_path)
		for item in all_remote_items:
			if is_ignorable(item['name']):
				print(item['name'] + ' is ignored.')
			
			elif item['type'] in self.api.FOLDER_TYPES:
				print(item['name'] + ' is a folder.')
				
				sub_path = local_path + item['name'] + '/'
				
				if not os.path.exists(sub_path):
					try: os.mkdir(sub_path)
					except OSError as exc:
						daemon_logger.critical('%s' % exc)
				elif not os.path.isdir(sub_path):
					# TODO: need to check if the local path is a file.
					pass
				
				self.queue.put((, item['id']))
			
			else:
				print(item['name'] + ' is a file.')
			
			print(item)
			if item['name'] in all_local_items: all_local_items.remove(item['name'])
		
		# process untouched local items
		for item in all_local_items:
			if is_ignorable(item):
				print(item + ' is ignorable.')
			elif os.path.isdir(local_path + item):
				print(item + ' is an untouched dir.')
			else:
				print(item + ' is an untouched file.')
		
	def sync(self):
		if self.running: return
		self.running = True
		while not self.queue.empty():
			entry = self.queue.get()
			self.merge_dir(entry)
			self.queue.task_done()
		daemon_logger.debug('queue is now empty.')
		self.running = False
	
class OneDrive_DaemonThread(threading.Thread):
	'''
	Daemon thread monitors the file system, and decides what task to issue
	to synchronizer.
	It also pulls data from the server periodically.
	'''
	def __init__(self, api, cv):
		super().__init__()
		self.name = 'daemon'
		self.daemon = True
		self.api = api
		self.cv = cv
		self.is_running = False
		# the daemon prints to stderr
		self.observer_list = []
		daemon_logger.info('there are ' + str(config.load_ignore_list()) + ' entries in the ignore list.')
	
	def on_task_complete(self, task_type, path):
		'''
		task_type should be one of: create, delete, move, copy, update
		'''
		# notify the observer
		for o in self.observer_list:
			o.handle_event(None, None)
	
	def on_inotify_task_created(self, task):
		path, event, name = task
		if 'CLOSE_WRITE' in event:
			# the given file is created or modified
			# put
			pass
		elif 'MOVED_TO' in event:
			# a file or dir is moved to the repo
			# renaming consists of two consecutive MOVE
			# put
			pass
		elif 'MOVED_FROM' in event:
			# a file or dir is moved out of the repo
			# including moved to trash
			# rm
			pass
		elif 'DELETE' in event:
			# a file is unlinked (deleted)
			# rm
			pass
		elif 'CREATE,ISDIR' == event:
			# a new dir is created
			# mkdir
			pass
		print(task)
	
	def run(self):
		daemon_logger.debug('start running.')
		self.is_running = True
		
		self.inotify_thread = OneDrive_INotifyThread(parent = self)
		self.inotify_thread.start()
		self.synchronizer = OneDrive_Synchronizer(api = self.api)
		
		# periodically run the deep sync work
		while self.is_running:
			self.cv.clear()
			if not self.synchronizer.is_busy():
				self.synchronizer.enqueue(config.APP_CONFIG['base_path'] + '/', self.api.get_root_entry_name())
				self.synchronizer.sync()
			self.cv.wait()
		self.inotify_thread.join()
		daemon_logger.debug('daemon shut down')
	
	def stop(self):
		self.inotify_thread.shut_down()
		self.is_running = False
	
	def add_observer(self, observer_obj):
		self.observer_list.append(observer_obj)
		observer_obj.set_daemon(self)
		daemon_logger.debug('added observer "' + observer_obj.name + '"')
	