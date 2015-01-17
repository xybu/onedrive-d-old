#!/usr/bin/python3

'''
Database manipulator classes for onedrive-d.
'''

import threading
import sqlite3
import od_glob

class TaskManager:
	lock = threading.Lock()
	db_name = 'tasks.db'
	
	def __init__(self):
		self.config = od_glob.get_config_instance()
		self.conn = sqlite3.connect(self.config.APP_CONF_PATH + '/' + TaskDatabase.db_name, isolation_level = None)
		self.cursor = self.conn.cursor()
		self.acquire_lock()
		self.cursor.execute('DROP TABLE IF EXISTS tasks')
		self.cursor.execute('''
			CREATE TABLE tasks
			(task_type TEXT, local_path TEXT, remote_id TEXT, remote_parent_id TEXT,
			priority INT DEFAULT 1, postwork TEXT,
			date_created TEXT DEFAULT CURRENT_TIMESTAMP PRIMARY KEY)
		''')
		self.conn.commit()
		self.release_lock()
	
	def acquire_lock(self):
		TaskDatabase.lock.acquire()
	
	def release_lock(self):
		TaskDatabase.lock.release()
	
	def add_task(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()
	
	def get_task(self):
		self.acquire_lock()
		
		self.release_lock()
	
	def del_task(self):
		self.acquire_lock()
		
		self.release_lock()
	
class EntryManager:
	lock = threading.Lock()
	db_name = 'entries.db'
	
	def __init__(self):
		self.config = od_glob.get_config_instance()
		self.conn = sqlite3.connect(self.config.APP_CONF_PATH + '/' + EntryDatabase.db_name, isolation_level = None)
		self.cursor = self.conn.cursor()
		self.acquire_lock()
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS entries
			(parent_path TEXT, name TEXT, type TEXT, id TEXT UNIQUE PRIMARY KEY, 
			parent_id TEXT PRIMARY_KEY, size INT, client_updated_time TEXT, status TEXT, 
			UNIQUE(parent_path, name) ON CONFLICT REPLACE)
		''')
		self.conn.commit()
		self.release_lock()
	
	def acquire_lock(self):
		EntryDatabase.lock.acquire()
	
	def release_lock(self):
		EntryDatabase.lock.release()
	
	def add_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()
	
	def get_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()
	
	def del_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()