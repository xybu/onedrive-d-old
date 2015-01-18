#!/usr/bin/python3

'''
Database manipulator classes for onedrive-d.
'''

import threading
import sqlite3
import od_glob

class TaskManager:
	'''
	Task manager abstracts the task queue implemented in SQLite to better
	control concurrency.
	
	task status: 0 (added), 1 (fetched), 2 (done, deletable)
	task types:
		for dirs: sy (sync), rm (remove), mk (mkdir on server)
		          tr (move local to trash).
		for files: up (upload), dl (download), mv (move), rm (remove)
		           cp (copy).
	'''
	# this semaphore counts the number of tasks in the table
	task_counter = threading.Semaphore(0)
	
	# mutex lock
	lock = threading.Lock()
	
	def __init__(self):
		self.logger = od_glob.get_logger()
		# enable auto-commit by setting isolation_level
		self.conn = sqlite3.connect('file::memory:?mode=memory&cache=shared', isolation_level = None, uri=True)
		self.cursor = self.conn.cursor()
		self.acquire_lock()
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS tasks
			(type TEXT, local_path TEXT, remote_id TEXT, remote_parent_id TEXT,
			status INT DEFAULT 0, date_created TEXT DEFAULT CURRENT_TIMESTAMP PRIMARY KEY)
		''')
		self.release_lock()
	
	def acquire_lock(self):
		TaskManager.lock.acquire()
	
	def release_lock(self):
		TaskManager.lock.release()
	
	def dec_sem(self):
		TaskManager.task_counter.acquire()
		self.logger.debug('decremented semaphore.')
	
	def inc_sem(self):
		TaskManager.task_counter.release()
		self.logger.debug('incremented semaphore.')
	
	def add_task(self, type, local_path, remote_id = '', remote_parent_id = '', status = 0):
		self.acquire_lock()
		self.cursor.execute('INSERT INTO tasks (type, local_path, remote_id, remote_parent_id, status) VALUES (?,?,?,?,?)', 
			(type, local_path, remote_id, remote_parent_id, status)
		)
		self.release_lock()
		self.inc_sem()
	
	def get_task(self):
		self.acquire_lock()
		self.cursor.execute('SELECT rowid, type, local_path, remote_id, remote_parent_id, status FROM tasks WHERE status=0 LIMIT 1')
		row = self.cursor.fetchone()
		if row == None: return None
		self.cursor.execute('UPDATE tasks SET status=1 WHERE rowid=?', (row[0], ))
		self.release_lock()
		data = {
			'type': row[1],
			'local_path': row[2],
			'remote_id': row[3],
			'remote_parent_id': row[4],
			'status': row[5],
		}
		return data
	
	def del_task(self):
		self.acquire_lock()
		
		self.release_lock()
	
	def dump(self):
		return self.conn.iterdump()
	
class EntryManager:
	lock = threading.Lock()
	db_name = 'entries.db'
	
	def __init__(self):
		self.config = od_glob.get_config_instance()
		self.logger = od_glob.get_logger()
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
		EntryManager.lock.acquire()
	
	def release_lock(self):
		EntryManager.lock.release()
	
	def add_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()
	
	def get_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()
	
	def del_entry(self, **kwargs):
		self.acquire_lock()
		
		self.release_lock()