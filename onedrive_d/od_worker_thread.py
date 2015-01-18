#!/usr/bin/python3

'''
Worker component of onedrive-d.

This component gets tasks from TaskManager and handles them,
and adds new tasks if needed.

When the task is about a file, it gets / puts / deletes the target
file. When the task points to a directory, it merges the local dir
with the remote entry.
'''

import os
import sys
import threading
import queue
import od_glob
import od_onedrive_api
import od_sqlite

class WorkerThread(threading.Thread):
	
	worker_list = queue.Queue()
	
	def __init__(self):
		super().__init__()
		self.name = 'worker_' + str(WorkerThread.worker_list.qsize())
		self.daemon = True
		self.logger = od_glob.get_logger()
		self.config = od_glob.get_config_instance()
		self.task_in_progress = threading.Event()
		self.task_in_progress.clear()
		# self.can_run = threading.Event()
		# self.can_run.set()
		WorkerThread.worker_list.put(self)
	
	def stop(self):
		pass
	
	def remove_dir(self, task):
		pass
	
	def sync_dir(self, task):
		entries = self.list_dir(task['local_path'])
		print(entries)
	
	def make_remote_dir(self, task):
		pass
	
	def trash_local_dir(self, task):
		pass
	
	def run(self):
		self.taskmgr = od_sqlite.TaskManager()
		while True:
			self.taskmgr.dec_sem()
			task = self.taskmgr.get_task()
			if task == None:
				self.logger.debug('got null task.')
				continue
			# this requires the dir to be created before the task is fetched.
			if os.path.isdir(task['local_path']):
				if task['type'] == 'sy': self.sync_dir(task)
				elif task['type'] == 'rm': self.remove_dir(task)
				elif task['type'] == 'mk': self.make_remote_dir(task)
				elif task['type'] == 'tr': self.trash_local_dir(task)
			else:
				# not a dir, then it is a file
				if task['type'] == 'up': pass
				elif task['type'] == 'dl': pass
				elif task['type'] == 'mv': pass
				elif task['type'] == 'rm': pass
				elif task['type'] == 'cp': pass
	
	def list_dir(self, path):
		'''
		Rename files with case conflicts and return the file list of the path.
		'''
		ent_list = []
		ent_count = {}
		entries = os.listdir(path)
		if self.config.ignore_list != None:
			entries = self.config.ignore_list.filter_list(entries, path)
		for ent in entries:
			ent_dup = ent.lower()
			if ent_dup in ent_count:
				ent_old = ent
				ent_count[ent_dup] += 1
				ent_name = os.path.splitext(ent)
				ent = ent_name[0] + ' (case_conflict_' + str(ent_count[ent_dup]) + ')' + ent_name[1]
				ent_dup = ent.lower()
				try:
					os.rename(path + '/' + ent_old, path + '/' + ent)
					ent_list.append(ent)
					ent_count[ent_dup] = 0
				except OSError as e:
					self.logger.error(e)
					# will not be added to entry list.
			else:
				ent_list.append(ent)
				ent_count[ent_dup] = 0
		return ent_list