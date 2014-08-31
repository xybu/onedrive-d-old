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
import sqlite3
import fnmatch
import config
import live_api

MAX_WORKER_NUM = 2
DAEMON_DB_PATH = config.APP_CONFIG_PATH + '/onedrive.sqlite'

def is_ignorable(name):
	for pattern in config.APP_IGNORE_LIST:
		if fnmatch.fnmatch(name, pattern): return True
	return False

def resolve_case_conflict(path):
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
	
def resolve_conflict(path, s = 'type_conflict', lst = None):
	'''
	Used to rename a file / folder to something else to solve type 
	inconsistency.
	
	@raises OSError
	
	But what if there is already a file called "sth (type_conflict)"?
	'''
	name, ext = os.path.splitext(path)
	new_path = name + ' (' + s + ')' + ext
	if lst != None and new_path in lst:
		i = 0
		while new_path in lst:
			i += 1
			new_path = name + ' (' + s + ', ' + i + ')' + ext
	os.rename(path, new_path)
	return os.path.basename(new_path)

def find_entry(cursor, criteria):
	wheres = []
	for k in criteria:
		wheres.append(k + '=:' + k)
	cursor.execute('SELECT * from entries WHERE ' + ' AND '.join(wheres), criteria)
	return cursor.fetchone()
	

def update_entry(cursor, entry):
	cursor.execute('INSERT OR REPLACE INTO entries (parent_path, name, id, '
		'parent_id, type, size, client_updated_time, status) VALUES '
		'(:parent_path, :name, :id, :parent_id, :type, :size, :client_updated_time, :status)', entry)

def add_work(cursor, type, path, remote_id = '', remote_parent_id = '', priority = 1, postwork = 'n'):
	cursor.execute('INSERT INTO tasks '
		'(task_type, local_path, remote_id, remote_parent_id, priority, date_created, postwork) VALUES '
		'(?, ?, ?, ?, ?, ?, ?)', (type, path, remote_id, remote_parent_id, priority, config.time_to_str(config.now()), postwork))

def add_notify(cursor, side, path, action):
	path = path.replace(config.APP_CONFIG['base_path'], '', 1)
	cursor.execute('INSERT INTO notifications '
		'(side, display_path, action, time) VALUES '
		'(?, ?, ?, ?)', (side, path, action, config.time_to_str(config.now())))

def remote_mkdir(api, cursor, parent_path, name, parent_id):
	try:
		new_dir_info = api.mkdir(name, parent_id)
		new_dir_info['type'] = 'folder'
		new_dir_info['size'] = 0
		new_dir_info['status'] = 'synced'
		new_dir_info['parent_path'] = parent_path
		update_entry(cursor, new_dir_info)
		add_notify(cursor, 'remote', parent_path + name, 'created')
	except live_api.OperationError as e:
		config.log.error(str(e))
	except live_api.NetworkError as e:
		config.log.error(str(e))

'''
INotifyThread and Synchronizer add tasks to the taskqueue.
SyncWorker consumes the tasks and notify the observers via daemon thread.
'''

class OneDrive_INotifyThread(threading.Thread):
	def __init__(self, switch, sem):
		super().__init__()
		self.name = 'inotify'
		self.daemon = True
		self.switch = switch
		self.sem = sem
		self.inotify_args = ['inotifywait', '-e', 'unmount,close_write,delete,move,isdir', '-cmr', config.APP_CONFIG['base_path']]
		if len(config.APP_IGNORE_LIST) > 0:
			ignore_list = []
			for item in config.APP_IGNORE_LIST:
				ignore_list.append(fnmatch.translate(item).replace('\\Z(?ms)', ''))
			self.inotify_args += ['--exclude', '(' +'|'.join(ignore_list) + ')']
	
	def on_task_created(self, task):
		self.sem.release()
		path, event, name = task
		config.log.info(str(task))
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
	
	def run(self):
		config.log.info('start running.')
		subp = subprocess.Popen(self.inotify_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while not self.switch.is_set():
			line = subp.stdout.readline().decode('utf-8')
			if line == '': time.sleep(1)
			elif line[0] == '/':
				line = line.rstrip()
				csv_rows = csv.reader(io.StringIO(line))
				for row in csv_rows:
					self.on_task_created(row)
		subp.terminate()
		subprocess.call(['kill', '-9', str(subp.pid)])
		config.log.info('inotify shut down.')

class OneDrive_SyncWorkerThread(threading.Thread):
	
	lock = threading.RLock()
	
	def __init__(self, name, parent, api, switch, sem):
		super().__init__()
		self.name = name
		self.daemon = True
		self.switch = switch
		self.sem = sem
		self.api = api
		self.parent = parent
	
	def find_entry(self, **kwargs):
		return find_entry(self.cursor, kwargs)
	
	def update_entry(self, entry):
		update_entry(self.cursor, entry)
		self.conn.commit()
	
	def add_notify(self, side, path, action):
		add_notify(self.cursor, side, path, action)
		self.conn.commit()
	
	def remote_mkdir(self, parent_path, name, parent_id):
		remote_mkdir(self.api, self.cursor, parent_path, name, parent_id)
		# this implicitly calls update_entry so the changes are committed.
	
	def fetch_one_task(self):
		OneDrive_SyncWorkerThread.lock.acquire()
		self.cursor.execute('SELECT * FROM tasks WHERE priority=1 ORDER BY date_created ASC LIMIT 1')
		row = self.cursor.fetchone()
		if row != None:
			self.cursor.execute('UPDATE tasks SET priority=0 WHERE id=?', (row['id'],))
			self.conn.commit()
		OneDrive_SyncWorkerThread.lock.release()
		return row
	
	def do_postwork(self, row, updated_info = None):
		parent_path, base_name = os.path.split(row['local_path'])
		
		if row['postwork'] == 'u':
			self.cursor.execute('UPDATE entries SET status="synced" WHERE parent_path=? AND name=?', (parent_path, base_name))
		elif row['postwork'] == 'n':
			if updated_info != None: id = updated_info['id']
			else: id = row['remote_id']
			new_info = self.api.get_property(id)
			new_info['type'] = 'file'
			new_info['status'] = 'synced'
			new_info['parent_path'] = parent_path
			self.update_entry(new_info)
		
		if row['task_type'] == 'get':
			# fix mtime
			entry = self.find_entry(parent_path = parent_path, name = base_name)
			assert entry != None
			t = config.str_to_timestamp(entry['client_updated_time'])
			os.utime(row['local_path'], (t, t))
		
		
	def run(self):
		config.log.info('worker starts running.')
		
		self.conn = sqlite3.connect(DAEMON_DB_PATH)
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()
		
		while True:
			self.sem.acquire()
			if self.switch.is_set(): break
			config.log.debug('I passed two locks.')
			row = self.fetch_one_task()
			if row == None: continue
			config.log.debug('I get a row from tasks table.')
			try:
				if row['task_type'] == 'get':
					config.log.info('Downloading "' + row['local_path'] + '".')
					f = open(row['local_path'], 'wb')
					f.write(self.api.get(entry_id = row['remote_id']))
					f.close()
					#new_mtime = timegm)
					#os.utime(t.p1, (new_mtime, new_mtime))
					self.do_postwork(row)
				elif row['task_type'] == 'put':
					config.log.info('Uploading "' + row['local_path'] + '".')
					update = self.api.put(name = os.path.basename(row['local_path']), 
						folder_id = row['remote_parent_id'], 
						local_path = row['local_path'])
					self.do_postwork(row, update)
				elif row['task_type'] == 'mkdir':
					local_path = row['local_path']
					config.log.info('Creating remote dir for "' + local_path + '"')
					if local_path.endswith('/'): local_path = local_path[:-1]
					parent_path, base_name = os.path.split(local_path)
					self.remote_mkdir(parent_path + '/', base_name, row['remote_parent_id'])
					# no special postwork to do
				elif row['task_type'] == 'rm':
					config.log.info('Delete remotely "' + row['local_path'] + '"')
					self.api.rm(entry_id = row['remote_id'])
					# TODO: update entries db.
				elif row['task_type'] == 'cp':
					config.log.info('Copying remotely "' + row['local_path'] + '" to dir "' + row['remote_parent_id'] + '"')
					self.api.cp(target_id = row['remote_id'], dest_folder_id = row['remote_parent_id'])
					# TODO: update entries db.
				elif row['task_type'] == 'mv':
					config.log.info('Copying remotely "' + row['local_path'] + '" to dir "' + row['remote_parent_id'] + '"')
					self.api.mv(target_id = row['remote_id'], dest_folder_id = row['remote_parent_id'])
					# TODO: update entries db.
				
				OneDrive_SyncWorkerThread.lock.acquire()
				self.cursor.execute('UPDATE tasks SET priority=priority-1 WHERE priority!=1')
				self.conn.commit()
				OneDrive_SyncWorkerThread.lock.release()
				
			#except live_api.OneDrive_Error as e:
			#	config.log.error(e.__class__.__name__ + ': ' + str(e))
			except OSError as e:
				config.log.error('OSError {0}: {1}. Path: {2}.'.format(e.errno, e.strerr, e.filename))
			
			self.parent.notify_all()
		
		self.conn.close()
		
		config.log.info('worker stops.')

class OneDrive_Synchronizer(threading.Thread):
	'''
	Note that the work to create a dir on remote during deep syncing
	has to be done by sync thread to make the work synced with the queue.
	'''
	def __init__(self, api, switch, sem):
		super().__init__()
		self.api = api
		self.name = 'syncer'
		self.daemon = True
		self.switch = switch
		self.sem = sem
		self.queue = queue.Queue()
		self.empty_lock = threading.Event()
		self.pending_work_count = 0
	
	def enqueue(self, local_path, remote_path):
		self.queue.put((local_path, remote_path))
		self.empty_lock.set()
	
	def remote_mkdir(self, parent_path, name, parent_id):
		remote_mkdir(self.api, self.cursor, parent_path, name, parent_id)
		self.enqueue(parent_path + name + '/', new_dir_info['id'])
	
	def add_work(self, type, path, remote_id = '', remote_parent_id = '', priority = 1, postwork = 'u'):
		add_work(self.cursor, type, path, remote_id, remote_parent_id, priority, postwork)
		self.pending_work_count += 1
		self.conn.commit()
	
	def add_notify(self, side, path, action):
		add_notify(self.cursor, side, path, action)
		self.conn.commit()
		# there is little value to have this notification displayed immediately
		# so do not tell daemon to notify observers
	
	def find_entry(self, **kwargs):
		return find_entry(self.cursor, kwargs)
	
	def update_entry(self, entry):
		update_entry(self.cursor, entry)
		self.conn.commit()
	
	def merge_dir(self, entry):
		'''
		A remote-first dir merge mechanism.
		'''
		local_path, remote_path = entry
		
		# if the dir does not exist locally, try creating it
		if not os.path.exists(local_path):
			try: config.mkdir(local_path)
			except OSError:
				pass
		
		config.log.info('syncing ' + local_path)
		
		all_remote_items = self.api.list_entries(remote_path)
		all_local_items = resolve_case_conflict(local_path)
		
		for item in all_remote_items:
			
			target_path = local_path + item['name']
			item['parent_path'] = local_path
			
			if is_ignorable(item['name']):
				config.log.info('Skipped remote entry "' + item['name'] + '"')
				pass
			elif item['type'] in self.api.FOLDER_TYPES:
				# if the item is a folder, resolve possible conflict
				# and then add it to the bfs queue.
				item['type'] = 'folder'
				item['size'] = 0
				item['status'] = 'synced'
				if os.path.isfile(target_path):
					confog.log.warning('"' + target_path + '" is a dir remotely, but file locally.')
					try:
						resolved_name = resolve_conflict(target_path)
						all_local_items.append(resolved_name)
					except OSError as e:
						config.log.error('OSError {0}: {1}. Path: {2}.'.format(e.errno, e.strerr, e.filename))
						continue
				self.update_entry(item)
				self.enqueue(target_path + '/', item['id'])
			else:
				# so the entry is a file
				# first check if the local file exists
				item['type'] = 'file'
				if os.path.isfile(target_path):
					# so both sides are files, compare their mtime
					try:
						local_mtime = config.timestamp_to_time(os.path.getmtime(target_path))
						remote_mtime = config.str_to_time(item['client_updated_time'])
						if local_mtime == remote_mtime:
							# same files, same timestamp
							# TODO: What if the files are different in content?
							item['status'] = 'synced'
							# config.log.debug(entry_local_path + ' was not changed. Skip.')
						elif local_mtime > remote_mtime:
							# local file is newer, upload it
							row = self.find_entry(parent_path = local_path, name = item['name'])
							if row != None and row['id'] == item['id'] and config.str_to_time(row['client_updated_time']) == remote_mtime:
								# the file is changed offline, and the remote one wasn't changed before.
								config.log.info('"' + target_path + ' is strictly newer. Upload it.')
								item['status'] = 'put'
								self.add_work('put', target_path, remote_parent_id = item['parent_id'], postwork='n')
							else:
								# the files are changed and no way to guarantee which one is abs newer.
								config.log.info('"' + target_path + ' is newer but conflicts can exist. Rename the local file.')
								item['status'] = 'get'
								try:
									new_name = resolve_conflict(target_path, config.OS_HOSTNAME + ', newer')
									all_local_items.append(new_name)
									self.add_work('get', target_path, remote_id = item['id'], postwork = 'n')
								except OSError as e:
									config.log.error('OSError {0}: {1}. Path: {2}.'.format(e.errno, e.strerr, e.filename))
						else:
							# in this branch the local file is older.
							row = self.find_entry(parent_path = local_path, name = item['name'])
							if row != None and row['id'] == item['id'] and config.str_to_time(row['client_updated_time']) == local_mtime:
								# so the remote file is absolutely newer
								# the local file wasn't changed when the program is off.
								config.log.info('"' + target_path + ' is strictly older. Download it.')
								item['status'] = 'get'
								self.add_work('get', target_path, remote_id = item['id'], postwork = 'u')
							else:
								config.log.info('"' + target_path + ' is older but conflicts can exist. Rename the local file.')
								item['status'] = 'get'
								try:
									new_name = resolve_conflict(target_path, config.OS_HOSTNAME + ', older')
									all_local_items.append(new_name)
									self.add_work('get', target_path, remote_id = item['id'], postwork = 'n')
								except OSError as e:
									config.log.error('OSError {0}: {1}. Path: {2}.'.format(e.errno, e.strerr, e.filename))
					except OSError as e:
						config.log.error('OSError {0}: {1}. Path: {2}.'.format(e.errno, e.strerr, e.filename))
				elif os.path.isdir(target_path):
					# the local file is a dir but the remote path is a file
					resolved_name = resolve_conflict(target_path)
					if resolved_name != None:
						all_local_items.append(resolved_name)
						itme['status'] = 'get'
						self.add_work('get', target_path, remote_id = item['id'], postwork = 'n')
					else:
						config.log.critical('"' + target_path + '" cannot sync because of non-resolvable type conflict.')
						continue
				else:
					# so the file does not exist locally.
					item['status'] = 'get'
					self.add_work('get', target_path, remote_id = item['id'], postwork = 'n')
				
				self.update_entry(item)
			
			if item['name'] in all_local_items:
				all_local_items.remove(item['name'])
		
		# process untouched local items
		for name in all_local_items:
			if is_ignorable(name): pass
			entry_record = self.find_entry(parent_path = local_path, name = name)
			if entry_record != None:
				config.log.debug('The entry "' + local_path + name + '" may have been deleted remotely but not reflected locally.')
				
			elif os.path.isdir(local_path + name):
				config.log.debug('Local dir "' + local_path + name + '" does not exist remotely. Create it.')
				
				self.remote_mkdir(local_path, item, remote_path)
			else:
				config.log.debug('Local file "' + local_path + name + '" does not exist remotely. Upload it.')
				self.add_work('put', local_path + name, remote_parent_id = remote_path, postwork = 'n')
		
		while self.pending_work_count > 0:
			self.sem.release()
			self.pending_work_count -= 1
	
	def restart(self):
		if self.queue.empty():
			config.log.info('restart the synchronizer.')
			# remove the old task records since they are not needed anymore.
			self.enqueue(config.APP_CONFIG['base_path'] + '/', self.api.get_root_entry_name())
			return True
		return False
	
	def stop(self):
		self.empty_lock.set()
	
	def run(self):
		config.log.info('syncer starts running')
		self.conn = sqlite3.connect(DAEMON_DB_PATH)
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()
		
		# when switch is set, the thread should stop
		while not self.switch.is_set():
			# block until there is something in the queue
			self.empty_lock.wait()
			while not self.switch.is_set() and not self.queue.empty():
				entry = self.queue.get()
				self.merge_dir(entry)
				self.queue.task_done()
			self.empty_lock.clear()
			config.log.debug('queue is now empty.')
		
		self.conn.close()
		config.log.info('syncer stops.')
	
class OneDrive_DaemonThread(threading.Thread):
	'''
	Daemon thread monitors the file system, and decides what task to issue
	to synchronizer.
	It also pulls data from the server periodically.
	
	The daemon should be initialized way before its child components get init-ed.
	'''
	def __init__(self, api, cv):
		super().__init__()
		self.name = 'daemon'
		self.daemon = True
		self.api = api
		self.cv = cv
		self.is_running = False
		self.observer_list = []
		self.worker_list = []
		self.children_lock = threading.Event()
		self.worker_sem = threading.Semaphore(0)
		config.log.info('there are ' + str(config.load_ignore_list()) + ' entries in the ignore list.')
	
	def notify_all(self):
		'''
		called in observer threads.
		'''
		for o in self.observer_list:
			o.notify()
	
	def run(self):
		config.log.debug('start running.')
		
		self.conn = sqlite3.connect(DAEMON_DB_PATH)
		self.cursor = self.conn.cursor()
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS entries 
			(parent_path TEXT, name TEXT, type TEXT, 
			id TEXT UNIQUE PRIMARY KEY, parent_id TEXT PRIMARY_KEY, 
			size INT, client_updated_time TEXT, status TEXT)
			''')
		# self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS local_path ON entries (parent_path, name)')
		self.cursor.execute('DROP TABLE IF EXISTS tasks')
		self.cursor.execute('''
			CREATE TABLE tasks 
			(id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT, 
			local_path TEXT, remote_id TEXT, remote_parent_id TEXT, 
			priority INT DEFAULT 1, postwork TEXT,
			date_created TEXT DEFAULT CURRENT_TIMESTAMP)
			''')
		self.cursor.execute('DROP TABLE IF EXISTS notifications')
		self.cursor.execute('''
			CREATE TABLE notifications 
			(side TEXT, display_path TEXT, action TEXT, 
			time TEXT DEFAULT CURRENT_TIMESTAMP)
			''')
		self.conn.commit()
		
		self.is_running = True
		
		self.sync_thread = OneDrive_Synchronizer(api = self.api, switch = self.children_lock, sem = self.worker_sem)
		self.sync_thread.start()
		self.inotify_thread = OneDrive_INotifyThread(switch = self.children_lock, sem = self.worker_sem)
		self.inotify_thread.start()
		
		for i in range(MAX_WORKER_NUM):
			w = OneDrive_SyncWorkerThread('worker ' + str(i), self, self.api, self.children_lock, self.worker_sem)
			self.worker_list.append(w)
			w.start()
		
		# periodically run the deep sync work
		while self.is_running:
			self.cv.clear()
			if self.sync_thread.restart():
				self.cursor.execute('DELETE FROM tasks WHERE priority<0')
				self.conn.commit()
			self.cv.wait()
		
		self.conn.close()
		
		for w in self.worker_list: w.join()
		self.sync_thread.stop()
		self.sync_thread.join()
		self.inotify_thread.join()
		
		config.log.debug('daemon shut down')
	
	def stop(self):
		'''
		stop() is called only in MainThread, its parent.
		'''
		self.cv.set()
		self.children_lock.set()
		for i in range(MAX_WORKER_NUM):
			self.worker_sem.release()
		self.is_running = False
	
	def add_observer(self, observer_obj):
		self.observer_list.append(observer_obj)
		config.log.debug('added observer "' + observer_obj.name + '"')
	