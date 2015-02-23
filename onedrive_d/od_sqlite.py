#!/usr/bin/python3

'''
Database manipulator classes for onedrive-d.
'''

import os
import threading
import sqlite3
from . import od_glob

class TaskManager:
	'''
	Task manager abstracts the task queue implemented in SQLite to better
	control concurrency.
	
	task status: 0 (added), 1 (fetched), 2 (done, deletable)
	task types:
		for dirs: sy (sync), rm (remove), mk (mkdir on server, postwork=[sy])
		          tr (move local to trash).
		for files: up (upload), dl (download, postwork=[add_row]), 
				mv (move), rf (remove), cp (copy).
	'''
	# this semaphore counts the number of tasks in the table
	task_counter = threading.Semaphore(0)
	
	# mutex lock
	lock = threading.Lock()

	db_initialized = False
	
	def __init__(self):
		self.logger = od_glob.get_logger()
		# enable auto-commit by setting isolation_level
		self.conn = sqlite3.connect('file::memory:?mode=memory&cache=shared', isolation_level = None, uri=True)
		self.cursor = self.conn.cursor()
		if not TaskManager.db_initialized:
			self.acquire_lock()
			self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS tasks
				(type TEXT, local_path TEXT, remote_id TEXT, remote_parent_id TEXT,
				status INT DEFAULT 0, args TEXT, extra_info TEXT, 
				UNIQUE(local_path, status) ON CONFLICT REPLACE)
			''')
			TaskManager.db_initialized = True
			self.release_lock()
	
	def acquire_lock(self):
		TaskManager.lock.acquire()
	
	def release_lock(self):
		TaskManager.lock.release()
	
	def dec_sem(self):
		TaskManager.task_counter.acquire()
		# self.logger.debug('decremented semaphore.')
	
	def inc_sem(self):
		TaskManager.task_counter.release()
		# self.logger.debug('incremented semaphore.')
	
	def add_task(self, type, local_path, remote_id = '', remote_parent_id = '', status = 0, args = '', extra_info = ''):
		# print(type + ' ' + local_path)
		self.acquire_lock()
		# delete old pending tasks for the file and add the new task at the end
		self.cursor.execute('DELETE FROM tasks WHERE local_path=? AND status=?', (local_path, status))
		self.cursor.execute('INSERT INTO tasks (type, local_path, remote_id, remote_parent_id, status, args, extra_info) VALUES (?,?,?,?,?,?,?)', 
			(type, local_path, remote_id, remote_parent_id, status, args, extra_info)
		)
		self.release_lock()
		self.inc_sem()
	
	def get_task(self):
		self.acquire_lock()
		self.cursor.execute('SELECT rowid, type, local_path, remote_id, remote_parent_id, status, args, extra_info FROM tasks WHERE status=0 ORDER BY rowid ASC LIMIT 1')
		row = self.cursor.fetchone()
		if row == None:
			self.release_lock()
			return None
		self.cursor.execute('UPDATE tasks SET status=1 WHERE rowid=?', (row[0], ))
		self.release_lock()
		data = {
			'task_id': row[0],
			'type': row[1],
			'local_path': row[2],
			'remote_id': row[3],
			'remote_parent_id': row[4],
			'status': row[5],
			'args': row[6],
			'extra_info': row[7]
		}
		return data
	
	def del_task(self, task_id):
		self.acquire_lock()
		self.cursor.execute('DELETE FROM tasks WHERE rowid=?', (task_id, ))
		self.release_lock()
	
	def dump(self):
		return self.conn.iterdump()
	
class EntryManager:
	lock = threading.Lock()
	db_name = 'entries.db'
	db_initialized = False
	
	def __init__(self):
		self.config = od_glob.get_config_instance()
		self.logger = od_glob.get_logger()
		self.conn = sqlite3.connect(self.config.APP_CONF_PATH + '/' + EntryManager.db_name, isolation_level = None)
		self.cursor = self.conn.cursor()
		if not EntryManager.db_initialized:
			self.acquire_lock()
			self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS entries
				(parent_path TEXT, name TEXT, isdir INT, remote_id TEXT UNIQUE PRIMARY KEY, 
				remote_parent_id TEXT PRIMARY_KEY, size INT, client_updated_time TEXT, status TEXT, 
				UNIQUE(parent_path, name) ON CONFLICT REPLACE)
			''')
			self.conn.commit()
			EntryManager.db_initialized = True
			self.release_lock()
	
	def acquire_lock(self):
		EntryManager.lock.acquire()
	
	def release_lock(self):
		EntryManager.lock.release()
	
	def update_entry(self, local_path, obj):
		'''
		Update an entry row in entries database.

		@param local_path: path to the local entry (MUST exist).
		@param obj: REST object returned by API.
		'''
		# print(obj)
		path, basename = os.path.split(local_path)
		isdir = os.path.isdir(local_path)
		if 'size' in obj: size = obj['size']
		else: size = 0
		self.acquire_lock()
		self.cursor.execute(
			'INSERT OR REPLACE INTO entries (parent_path, name, isdir, remote_id, remote_parent_id, size, client_updated_time, status) VALUES (?,?,?,?,?,?,?,?)',
			(path, basename, isdir, obj['id'], obj['parent_id'], size, obj['client_updated_time'], ''))
		self.release_lock()
	
	def update_local_path(self, old_path, new_path):
		path, basename = os.path.split(old_path)
		new_path, new_basename = os.path.split(new_path)
		self.acquire_lock()
		self.cursor.execute('UPDATE entries SET parent_path=?, name=? WHERE parent_path=? AND name=?', 
			(new_path, new_basename, path, basename))
		self.release_lock()

	def get_entry(self, isdir, local_path = '', remote_id = None):
		'''
		At least one of local_path and remote_id should be given.
		'''
		if local_path == '':
			where = 'remote_id=?'
			cond = (isdir, remote_id)
		else:
			path, basename = os.path.split(local_path)
			if remote_id == None:
				where = 'parent_path=? AND name=?'
				cond = (isdir, path, basename)
			else:
				where = 'parent_path=? AND name=? AND remote_id=?'
				cond = (isdir, path, basename, remote_id)

		self.acquire_lock()
		self.cursor.execute('SELECT rowid, parent_path, name, isdir, remote_id, remote_parent_id, size, client_updated_time, status FROM entries WHERE isdir=? AND ' + where, 
			cond)
		row = self.cursor.fetchone()
		self.release_lock()
		if row == None: return None
		data = {
			'entry_id': row[0],
			'parent_path': row[1],
			'name': row[2],
			'isdir': row[3],
			'remote_id': row[4],
			'remote_parent_id': row[5],
			'size': row[6],
			'client_updated_time': row[7],
			'status': row[8]
		}
		return data
	
	def del_entry_by_remote_id(self, remote_id):
		self.acquire_lock()
		self.cursor.execute('DELETE FROM entries WHERE remote_id=?', (remote_id, ))
		self.release_lock()

	def del_entry_by_path(self, local_path):
		path, basename = os.path.split(local_path)
		self.acquire_lock()
		self.cursor.execute('DELETE FROM entries WHERE parent_path=? AND name=?', (path, basename))
		self.release_lock()	

	def del_entry_by_parent(self, parent_path = None, remote_parent_id = None):
		self.acquire_lock()
		if remote_parent_id != None:
			# this one does not simulate recursive deletion
			self.cursor.execute('DELETE FROM entries WHERE remote_parent_id=?', (remote_parent_id, ))
		if parent_path != None:
			# this one simulates recursive deletion
			path, basename = os.path.split(parent_path)
			self.cursor.execute('DELETE FROM entries WHERE parent_path LIKE ? OR parent_path=?', (parent_path + '/%', parent_path))
			self.cursor.execute('DELETE FROM entries WHERE parent_path=? AND name=?', (path, basename))
		self.release_lock()