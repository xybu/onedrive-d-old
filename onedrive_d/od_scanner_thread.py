#!/usr/bin/python3

'''
Scanner component of onedrive-d.

Starting from the local OneDrive root dir and remote OneDrive root dir, compare 
the differences and emit sync requests if any difference is found.

'''

import os
import sys
import threading
import queue
import od_glob
import od_onedrive_api

class ScannerThread(threading.Thread):
	
	def __init__(self):
		super().__init__()
		self.name = 'scanner'
		self.daemon = True
		self.dir_queue = queue.Queue()
		self.logger = od_glob.get_logger()
		self.api = od_onedrive_api.get_instance()
		self.config = od_glob.get_config_instance()
		self.running = threading.Event()
		self.running.set()
	
	def exit(self):
		'''
		Called by an external thread to stop the execution of 
		the while loop.
		'''
		self.running.clear()
	
	def enqueue(self, local_path, remote_path):
		'''
		Called both internally and externally.
		'''
		self.dir_queue.put((local_path, remote_path))
	
	def resolve_case_conflict(self, path):
		'''
		Rename files with case conflicts and return the file list of the path.
		'''
		ent_count = {}
		ent_list = []
		entris = os.listdir(path)
		path = path + '/'
		for ent in entris:
			ent_lower = ent.lower()
			if ent_lower in ent_count:
				# case conflict
				ent_count[ent_lower] = 1
				file_name = os.path.splitext(ent)
				ent_new = file_name[0] + ' (case_conflict_' + str(ent_count[ent_lower]) + ')' + file_name[1]
				os.rename(path + ent, path + ent_new)
				ent = ent_new
			else:
				ent_count[ent_lower] = 0
				ent_list.append(ent)
		del ent_count
		return ent_list
	
	def run(self):
		
		while self.running.is_set():
			
			local_path, remote_path = self.dir_queue.get()
			self.dir_queue.task_done()
			
			if not os.path.exists(local_path):
				try: od_glob.mkdir(local_path, self.config.OS_USER_ID)
				except OSError as e:
					self.logger.critical('OSError: {}' % e)
					continue
			
			print(local_path)
			
			#remote_items = self.api.list_entries(remote_path)
			#local_items = self.resolve_case_conflict(local_path)
			