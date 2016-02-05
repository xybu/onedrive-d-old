#!/usr/bin/python3

"""
Worker component of onedrive-d.

This component gets tasks from TaskManager and handles them,
and adds new tasks if needed.

When the task is about a file, it gets / puts / deletes the target
file. When the task points to a directory, it merges the local dir
with the remote entry.
"""

import os
import sys
import json
import threading
import queue
from send2trash import send2trash
from . import od_glob
from . import od_inotify_thread
from . import od_onedrive_api
from . import od_sqlite


class WorkerThread(threading.Thread):

	worker_list = []
	worker_lock = threading.Lock()
	logger = od_glob.get_logger()
	config = od_glob.get_config_instance()
	api = od_onedrive_api.get_instance()

	def __init__(self):
		super().__init__()
		self.daemon = True
		self.running = True
		self.is_busy = False
		WorkerThread.worker_lock.acquire()
		self.name = 'worker' + str(len(WorkerThread.worker_list))
		WorkerThread.worker_list.append(self)
		WorkerThread.worker_lock.release()

	def stop(self):
		self.running = False

	def remove_dir(self, task):
		if os.path.exists(task['local_path']) and os.path.isdir(task['local_path']):
			try:
				send2trash(task['local_path'])
			except OSError as e:
				self.logger.error(e)
		if not os.path.exists(task['local_path']):
			self.api.rm(task['remote_id'])
			self.entrymgr.del_entry_by_parent(task['local_path'])
		self.taskmgr.del_task(task['task_id'])

	def remove_file(self, task):
		if os.path.exists(task['local_path']) and os.path.isfile(task['local_path']):
			try:
				send2trash(task['local_path'])
			except OSError as e:
				self.logger.error(e)
		if not os.path.exists(task['local_path']):
			self.api.rm(task['remote_id'])
			self.entrymgr.del_entry_by_remote_id(task['remote_id'])
		self.taskmgr.del_task(task['task_id'])

	def sync_dir(self, task):

		try:
			local_entries = self.list_dir(task['local_path'])
		except OSError as e:
			self.logger.error(e)
			self.taskmgr.del_task(task['task_id'])
			return

		remote_entries = self.api.list_entries(folder_id=task['remote_id'])
		is_recursive_task = 'recursive,' in task['args']

		for entry in remote_entries:

			# skip the entry if ignorable
			if self.config.ignore_list and \
					self.config.ignore_list.is_ignorable(entry['name'], task['local_path']):
				continue

			local_path = task['local_path'] + '/' + entry['name']

			if entry['type'] in self.api.FOLDER_TYPES:
				# remote entry is a directory

				if entry['name'] in local_entries and os.path.isfile(local_path):
					# remote entry is a dir but local entry is a file
					new_path = self.resolve_type_conflict(local_path, isdir=False)
					if new_path is None:
						self.logger.critical(
							'entry "' + local_path + '" is remotely a dir but locally a file. Rename failed. Skip.')
						local_entries.remove(entry['name'])
						# self.taskmgr.del_task(task['task_id'])
						continue
					else:
						# TODO: can there be a local-remote correspondance to handle?
						previous_entry = self.entrymgr.get_entry(
							isdir=False, local_path=local_path)
						if previous_entry is not None:
							# if we update entry, the file will be sent to trash if not modified
							# self.entrymgr.update_local_path(local_path, new_path)
							# deleting the entry record will have the renamed file uploaded
							self.entrymgr.del_entry_by_remote_id(previous_entry['remote_id'])

						# replace the old name with new name
						local_entries.remove(entry['name'])
						local_entries.append(os.path.basename(new_path))

				if entry['name'] not in local_entries:
					# TODO: should determine if it is a deleted entry.
					previous_entry = self.entrymgr.get_entry(
						isdir=True, local_path=local_path)
					if previous_entry is not None and previous_entry['remote_id'] == entry['id'] and previous_entry['client_updated_time'] == entry['client_updated_time']:
						# server and prev record match, but the dir is deleted
						# this includes handling 'MOVED_FROM'
						if previous_entry['status'] == 'MOVED_FROM':
							# delete the record to force MOVED_TO to do upload action.
							self.entrymgr.del_entry_by_remote_id(previous_entry['remote_id'])
						self.taskmgr.add_task('rm', local_path=local_path, remote_id=entry['id'], remote_parent_id=entry['parent_id'])
						# local_entries.remove(entry['name'])
						continue
					# this is a dir that exists remotely but not locally
					try:
						self.logger.debug(
							'local dir "' + local_path + '" does not exist. Creating it.')
						od_glob.mkdir(local_path, self.config.OS_USER_ID)
						local_entries.append(entry['name'])
					except OSError as e:
						self.logger.error(e)
						self.logger.error(
							'failed to create local dir "' + local_path + '". Skip the remote entry.')
						# self.taskmgr.del_task(task['task_id'])
						continue

				self.entrymgr.update_entry(local_path, entry)

				if is_recursive_task:
					self.taskmgr.add_task(type=task['type'], local_path=local_path, remote_id=entry['id'], remote_parent_id=entry['parent_id'], args=task['args'])

				local_entries.remove(entry['name'])
			elif entry['type'] not in self.api.UNSUPPORTED_TYPES:
				# remote entry is a file
				if entry['name'] in local_entries and os.path.isdir(local_path):
					# remote entry is a file but local one is dir
					new_path = self.resolve_type_conflict(local_path, isdir=True)
					if new_path is None:
						self.logger.critical(
							'entry "' + local_path + '" is remotely a file but locally a dir. Rename failed. Skip.')
						local_entries.remove(entry['name'])
						# self.taskmgr.del_task(task['task_id'])
						continue
					else:
						# previous_entry = self.entrymgr.get_entry(isdir = True, local_path = local_path)
						# if previous_entry is not None:
						# 	self.entrymgr.update_local_path(local_path, new_path)
						# replace the old name with new name
						# local_entries.remove(entry['name'])
						local_entries.append(os.path.basename(new_path))
				self.analyze_file_path(local_path, task['remote_id'], entry, local_entries)
				if entry['name'] in local_entries:
					local_entries.remove(entry['name'])
			else:
				self.logger.warning('skipped file "' + task['local_path'] + '/' + entry['name'] + '" of unsupported type "' + entry['type'] + '".')

		for ent_name in local_entries:
			# untouched local files
			local_path = task['local_path'] + '/' + ent_name
			if os.path.isdir(local_path):
				previous_entry = self.entrymgr.get_entry(isdir=True, local_path=local_path)
				if previous_entry is not None:
					if previous_entry['status'] == 'MOVED_TO':
						# the old record marks a movement
						# propagate to server
						self.taskmgr.add_task('mv', local_path, remote_id=previous_entry['remote_id'], remote_parent_id=previous_entry['remote_parent_id'])
					else:
						# there was an old record about this dir before
						# but now the dir in remote is gone
						try:
							send2trash(local_path)
							self.entrymgr.del_entry_by_parent(parent_path=local_path)
						except OSError as e:
							self.logger.error(e)
				else:
					# probably a dir that was newly created
					self.taskmgr.add_task(
						'mk', local_path, remote_parent_id=task['remote_id'], args='sy,recursive,')
			else:
				# we can pass local_entries during the iteration because the branch to run
				# in analyze_file_path will not modify local_entries.
				self.analyze_file_path(local_path, task['remote_id'], None, local_entries)

		self.taskmgr.del_task(task['task_id'])

	def analyze_file_path(self, local_path, remote_parent_id, entry, local_entries):
		"""
		@param local_path: path either pointing to a file or DNE.
		"""
		try:
			is_exist = os.path.exists(local_path)
		except UnicodeEncodeError:
			self.logger.error('Failed to stat entry "%s". Path is not Unicode.', local_path)
			return
		previous_entry = self.entrymgr.get_entry(isdir=False, local_path=local_path)
		if not is_exist and entry is not None:
			if previous_entry is not None and previous_entry['remote_id'] == entry['id'] and previous_entry['client_updated_time'] == entry['client_updated_time']:
				# remote record exists, previous record exists, same record, but file doesn't exist.
				# the file is more likely to be deleted when daemon is off,
				# or the file is MOVED_FROM.
				# if the file sync comes before MOVED_TO, the MOVED_TO should be reduced to an upload action
				# otherwise MOVED_TO will do mv/cp task.
				if previous_entry['status'] == 'MOVED_FROM':
					# delete the record to force MOVED_TO to do upload action.
					self.entrymgr.del_entry_by_remote_id(previous_entry['remote_id'])
				self.taskmgr.add_task('rf', local_path, entry['id'], entry['parent_id'])
			else:
				# no previous record,
				# or prev record exists, but its points to a different entry,
				# or prev record exists, and same entry, but timestamps differ (local is
				# older for sure).
				self.taskmgr.add_task('dl', local_path, entry['id'], entry['parent_id'], args='add_row,', extra_info=json.dumps(entry))
		elif is_exist:
			# the file exists
			try:
				local_mtime = od_glob.timestamp_to_time(os.path.getmtime(local_path))
				local_fsize = os.path.getsize(local_path)
			except OSError as e:
				self.logger.error(e)
				return

			if entry is None:
				# no remote record given for analysis
				if previous_entry is not None:
					if previous_entry['status'] == 'MOVED_TO':
						self.taskmgr.add_task('mv', local_path,
							remote_id=previous_entry['remote_id'],
							remote_parent_id=previous_entry['remote_parent_id'])
					else:
						# the file existed on server before, but not found on server this time
						remote_mtime = od_glob.str_to_time(previous_entry['client_updated_time'])
						if local_mtime != remote_mtime:
							# but the file was changed after last sync. Better upload than delete.
							self.taskmgr.add_task('up', local_path, remote_parent_id=remote_parent_id)
						else:
							# the file wasn't modified after it was last recorded. Delete it
							# locally.
							try:
								self.logger.info('sending file "' + local_path + '" to trash.')
								send2trash(local_path)
								self.entrymgr.del_entry_by_remote_id(previous_entry['remote_id'])
							except OSError as e:
								self.logger.error(e)
								return
				else:
					# no local record either, most likely it is a new file
					self.taskmgr.add_task('up', local_path, remote_parent_id=remote_parent_id)
			else:
				# both file and remote record exist
				remote_mtime = od_glob.str_to_time(entry['client_updated_time'])
				if previous_entry is None:
					# no previous record for reference
					# always keep both because we cannot determine from mtime and file size
					if local_mtime == remote_mtime and local_fsize == entry['size']:
						# same mtime and file size, hopefully we can trust they are the same
						# just fix the record
						self.entrymgr.update_entry(local_path=local_path, obj=entry)
					else:
						self.logger.warning('case1: ' + str(local_mtime) + ',' +
											str(local_fsize) + ' vs ' + str(remote_mtime) + ',' + str(entry['size']))
						new_path = self.resolve_conflict(local_path, self.config.OS_HOSTNAME)
						if new_path is None:
							self.logger.critical('cannot rename file "' + local_path + '" to avoid conflict. Skip the conflicting remote file.')
							return
						# add the renamed local file to list so as to upload it later
						local_entries.append(os.path.basename(new_path))
						# download the remote file to the path
						self.taskmgr.add_task('dl', local_path, entry['id'], entry['parent_id'], args='add_row,', extra_info=json.dumps(entry))
				else:
					# we have a previous record for reference
					if previous_entry['remote_id'] == entry['id']:
						# at least they are the same entry
						if local_mtime > remote_mtime and entry['client_updated_time'] == previous_entry['client_updated_time']:
							# the local file is strictly newer, so upload it
							self.taskmgr.add_task('up', local_path, entry['id'], entry['parent_id'])
						elif local_mtime < remote_mtime and local_mtime == od_glob.str_to_time(previous_entry['client_updated_time']):
							# the remote entry is strictly newer, so download it
							self.taskmgr.add_task('dl', local_path, entry['id'], entry['parent_id'], args='add_row,', extra_info=json.dumps(entry))
						elif local_mtime != remote_mtime or entry['client_updated_time'] != previous_entry['client_updated_time']:
							# there may be more than one revisions between them
							# better keep both
							self.logger.warning('case2: ' + str(local_mtime) + ',' +
												str(local_fsize) + ' vs ' + str(remote_mtime) + ',' + str(entry['size']))
							new_path = self.resolve_conflict(local_path, self.config.OS_HOSTNAME)
							if new_path is None:
								self.logger.critical('cannot rename file "' + local_path + '" to avoid conflict. Skip the conflicting remote file.')
								return
							# add the renamed local file to list so as to upload it later
							local_entries.append(os.path.basename(new_path))
							# the existing entry record will be for the downloaded file
							# the renamed file will be treated as a newly created file later
							# download the remote file to the path
							self.taskmgr.add_task('dl', local_path, entry['id'], entry['parent_id'], args='add_row,', extra_info=json.dumps(entry))
						else:
							# local record and remote record match perfectly
							pass
					else:
						# same path, but no longer same entry seen by server
						# one must have replaced the other
						if local_mtime != od_glob.str_to_time(previous_entry['client_updated_time']):
							# the local file was modified since its last sync
							# better keep it
							self.logger.warning('case3: ' + str(local_mtime) + ',' + str(local_fsize) + ' vs ' + str(
								od_glob.str_to_time(previous_entry['client_updated_time'])) + ',' + str(previous_entry['size']))
							new_path = self.resolve_conflict(local_path, self.config.OS_HOSTNAME)
							if new_path is None:
								self.logger.critical('cannot rename file "' + local_path + '" to avoid conflict. Skip the conflicting remote file.')
								return
							local_entries.append(os.path.basename(new_path))
						# else:
							# the local file was not modified since its last sync
							# so the user must have replaced it with the remote one
						# 	pass
						self.taskmgr.add_task('dl', local_path, entry['id'], entry['parent_id'], args='add_row,', extra_info=json.dumps(entry))
		else:
			# the file does not exist, and there is no remote entry
			# there must be logical bug calling this function
			raise Exception(
				"analyze_file_path: local_path and entry cannot both be NULL.")

	def make_remote_dir(self, task):
		if os.path.exists(task['local_path']):
			name = os.path.basename(task['local_path'])
			new_entry = self.api.mkdir(name, task['remote_parent_id'])
			self.entrymgr.update_entry(task['local_path'], new_entry)
			if 'sy,' in task['args']:
				if 'recursive,' in task['args']:
					is_recursive_task = 'recursive,'
				else:
					is_recursive_task = ''
				self.taskmgr.del_task(task['task_id'])
				self.taskmgr.add_task(type='sy', local_path=task['local_path'],
					remote_id=new_entry['id'], remote_parent_id=task['remote_parent_id'],
					args=is_recursive_task)
		else:
			self.taskmgr.del_task(task['task_id'])

	def upload_file(self, task):
		try:
			local_fsize = os.path.getsize(task['local_path'])
		except OSError as e:
			self.logger.error(e)
			self.taskmgr.del_task(task['task_id'])
			return
		parent_path, basename = os.path.split(task['local_path'])
		if local_fsize >= self.config.params['BITS_FILE_MIN_SIZE']:
			# remote_path = task['local_path'][len(self.config.params['ONEDRIVE_ROOT_PATH']) + 1:]
			new_entry = self.api.bits_put(basename,
				folder_id=task['remote_parent_id'],
				local_path=task['local_path'],
				# remote_path = remote_path,
				block_size=self.config.params['BITS_BLOCK_SIZE'])
			if new_entry is None:
				self.logger.error('failed to BITS upload "' + task['local_path'] + '".')
				self.taskmgr.del_task(task['task_id'])
				return
		else:
			new_entry = self.api.put(basename,
				folder_id=task['remote_parent_id'],
				local_path=task['local_path'])
			# new_entry['parent_id'] = task['remote_parent_id']
		# fix timestamp
		self.entrymgr.update_entry(task['local_path'], new_entry)
		try:
			t = od_glob.str_to_timestamp(new_entry['client_updated_time'])
			os.utime(task['local_path'], (t, t))
		except OSError as e:
			self.logger.error(e)
		self.taskmgr.del_task(task['task_id'])

	def download_file(self, task):
		entry = json.loads(task['extra_info'])
		if entry['size'] >= self.config.params['BITS_FILE_MIN_SIZE']:
			# download large files by blocks
			if not self.api.get_by_blocks(task['remote_id'], task['local_path'], entry['size'], self.config.params['BITS_BLOCK_SIZE']):
				self.logger.error(
					'failed to download to file "%s" by blocks.', task['local_path'])
				self.taskmgr.del_task(task['task_id'])
				return
		else:
			# use single HTTP request to download small files
			if not self.api.get(task['remote_id'], task['local_path']):
				self.logger.error('failed to download file "%s".', task['local_path'])
				self.taskmgr.del_task(task['task_id'])
				return
		if 'add_row,' in task['args']:
			self.entrymgr.update_entry(task['local_path'], entry)
		try:
			t = od_glob.str_to_timestamp(entry['client_updated_time'])
			os.utime(task['local_path'], (t, t))
		except OSError as e:
			self.logger.error(e)
		self.taskmgr.del_task(task['task_id'])

	def move_remote_entry(self, task):
		if os.path.exists(task['local_path']):
			new_entry = self.api.mv(target_id=task['remote_id'],
				dest_folder_id=task['remote_parent_id'])
			self.entrymgr.update_entry(task['local_path'], new_entry)
			if os.path.isdir(task['local_path']):
				self.entrymgr.update_parent_path_by_parent_id(
					task['local_path'], new_entry['id'])
			try:
				t = od_glob.str_to_timestamp(new_entry['client_updated_time'])
				os.utime(task['local_path'], (t, t))
			except OSError as e:
				self.logger.error(e)
		self.taskmgr.del_task(task['task_id'])

	def run(self):
		self.taskmgr = od_sqlite.TaskManager()
		self.entrymgr = od_sqlite.EntryManager()
		while self.running:		# not self.stop_event.is_set():
			self.taskmgr.dec_sem()
			task = self.taskmgr.get_task()
			if task is None:
				self.logger.debug('got null task.')
				continue

			self.logger.debug('got task: %s on "%s"', task['type'], task['local_path'])

			self.is_busy = True
			od_inotify_thread.INotifyThread.pause_event.set()
			if task['type'] == 'sy':
				self.sync_dir(task)
			elif task['type'] == 'rm':
				self.remove_dir(task)
			elif task['type'] == 'mk':
				self.make_remote_dir(task)
			elif task['type'] == 'up':
				self.upload_file(task)
			elif task['type'] == 'dl':
				self.download_file(task)
			elif task['type'] == 'mv':
				self.move_remote_entry(task)
			elif task['type'] == 'rf':
				self.remove_file(task)
			elif task['type'] == 'af':
				pass
			elif task['type'] == 'cp':
				pass
			else:
				raise Exception('Unknown task type "' + task['type'] + '".')
			od_inotify_thread.INotifyThread.pause_event.clear()
			self.is_busy = False
		self.taskmgr = None
		self.entrymgr.close()
		self.logger.debug('stopped.')

	def list_dir(self, path):
		"""
		Rename files with case conflicts and return the file list of the path.
		"""
		ent_list = []
		ent_count = {}
		entries = os.listdir(path)
		if self.config.ignore_list is not None:
			entries = self.config.ignore_list.filter_list(entries, path)
		for ent in entries:
			ent_dup = ent.lower()
			if ent_dup in ent_count:
				ent_old = ent
				ent_count[ent_dup] += 1
				ent_name = os.path.splitext(ent)
				ent = ent_name[
					0] + ' (case_conflict_' + str(ent_count[ent_dup]) + ')' + ent_name[1]
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

	def resolve_type_conflict(self, path, isdir):
		if isdir:
			t = 'dir'
		else:
			t = 'file'
		return self.resolve_conflict(path, t)

	def resolve_conflict(self, path, t):
		"""
		Append a type flag after the entry name when
			* the remote entry is a dir while the local entry is a file, or
			* when the remote entry is a file while the local entry is a dir.

		@param path: the local file path
		@param isdir: previously calculated os.path.isdir(path)

		@return None if failed to rename
		@return new_path if renaming succeeds.
		"""
		name, ext = os.path.splitext(path)
		new_path = name + ' (' + t + ')' + ext
		if not os.path.exists(new_path):
			try:
				os.rename(path, new_path)
				return new_path
			except OSError as e:
				self.logger.error(e)
				return None
		else:
			i = 1
			while True:
				new_path = name + ' (' + t + ', ' + str(i) + ')' + ext
				if not os.path.exists(new_path):
					try:
						os.rename(path, new_path)
						return new_path
					except OSError as e:
						self.logger.error(e)
						return None
				i += 1
