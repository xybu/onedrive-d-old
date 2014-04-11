#!/usr/bin/python

import os
import sys
import time
import re
import gc
import threading
import Queue
import subprocess
import signal
import StringIO
import csv
from config import *
from calendar import timegm
from dateutil import parser
from onedrive import api_v5

TEMP_EXCLUSION_LIST = []
TEMP_EXCLUSION_LOCK = threading.Lock()

# rename files that have same name in lowecase
# and return a dictionary of the new file names
def resolve_CaseConflict(path):
	_ent_dict = {}
	_ent_list = []
	ents = os.listdir(path)
	path = path + "/"
	for item in ents:
		item_l = item.lower()
		if item_l in _ent_dict:
			# case conflict
			_ent_dict[item_l] += 1
			count = _ent_dict[item_l]
			ext_dot_pos = item.rfind(".")
			if ext_dot_pos == -1:
				os.rename(path + item, path + item + " (CONFLICT_" + str(count) + ")")
				item = item + " (CONFLICT_" + str(count) + ")"
			else:
				item_new = item[0:ext_dot_pos:] + " (CONFLICT_" + str(count) + ")" + item[ext_dot_pos:len(item)]
				os.rename(path + item, path + item_new)
			item_l = item.lower()
		_ent_dict[item_l] = 0
		_ent_list.append(item)
	del _ent_dict
	return _ent_list

class Task():
	def __init__(self, type, p1, p2, timeStamp = None):
		self.type = type
		self.p1 = p1 # mostly used as a local path
		self.p2 = p2 # mostly used as a remote path
		if timeStamp!= None:
			self.timeStamp = timeStamp	# time, etc.
	
	def debug(self):
		return "Task(" + self.type + ", " + self.p1 + ", " + self.p2 + ")"

class TaskWorker(threading.Thread):
	WORKER_SLEEP_INTERVAL = 3 # in seconds
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		print(self.getName() + " (worker): initiated")
	
	def getArgs(self, t):
		return {
			"mv": ["mv", t.p1, t.p2],
			"mkdir": ["mkdir", t.p2],	# mkdir path NOT RECURSIVE!
			"get": ["get", t.p2, t.p1],	# get remote_file local_path
			"put": ["put", t.p1, t.p2],	# put local_file remote_dir
			"cp": ["cp", t.p1, t.p2],	# cp file folder
			"rm": ["rm", t.p2]
		}[t.type]
	
	def getMessage(self, t):
		pass
	
	def consume(self, t):
		args = self.getArgs(t)
		subp = subprocess.Popen(['onedrive-cli'] + args, stdout=subprocess.PIPE)
		ret = subp.communicate()
		
		# post-work
		if t.type == "get":
			old_mtime = os.stat(t.p1).st_mtime
			new_mtime = timegm(parser.parse(t.timeStamp).utctimetuple())
			os.utime(t.p1, (new_mtime, new_mtime))
			new_old_mtime = os.stat(t.p1).st_mtime
			print(self.getName() + ": " + t.p1 + " Old_mtime is " + str(old_mtime) + " and new_mtime is " + str(new_mtime) + " and is changed to " + str(new_old_mtime))
		elif t.type == "mkdir" and t.p1 != "":
			# upload the local dir to remote
			# correspond to scanner's post_merge
			_ent_list = resolve_CaseConflict(t.p1)
			for entry in _ent_list:
				if "exclude" in CONF != "" and re.match(CONF["exclude"], entry):
					print(t.p1 + "/" + entry + " is excluded by worker.")
				elif os.path.isfile(t.p1 + "/" + entry):
					TASK_QUEUE.put(Task("put", t.p1 + "/" + entry, t.p2 + "/" + entry))
				else:	# a dir
					TASK_QUEUE.put(Task("mkdir", t.p1 + "/" + entry, t.p2 + "/" + entry))
		
		if ret[0] != None and ret[0] != "":
			print("subprocess stdout: " + ret[0])
		if ret[1] != None and ret[0] != "":
			print("subprocess stderr: " + ret[1])
		print(self.getName() + ": executed task: " + t.debug())
		
		AGENT.add_message(title = "OneDrive-d", text = t.p2 + " was updated.")
		del t
	
	def run(self):
		while True:
			if EVENT_STOP.is_set():
				break
			elif TASK_QUEUE.empty():
				time.sleep(self.WORKER_SLEEP_INTERVAL)
			else:
				task = TASK_QUEUE.get()
				self.consume(task)
				del task
				TASK_QUEUE.task_done()

# DirScanner represents either a file entry or a dir entry in the OneDrive repository
# it uses a single thread to process a directory entry
class DirScanner(threading.Thread):
	def __init__(self, localPath, remotePath):
		threading.Thread.__init__(self)
		SCANNER_QUEUE.put(self)
		self.daemon = True
		self._localPath = localPath
		self._remotePath = remotePath
		self._raw_log = None
	
	def ls(self):
		SCANNER_SEMA.acquire()
		print(self.getName() + ": Start scanning dir " + self._remotePath + " (\"" + self._localPath + "\")")
		try:
			self._raw_log = list(API.listdir(API.resolve_path(self._remotePath)))
		except api_v5.DoesNotExists as e:
			print("Remote path \"" + self._remotePath + "\" does not exist.\n({0}): {1}".format(e.errno, e.strerror))
		except api_v5.AuthenticationError as e:
			print("Authentication failed.\n({0}): {1}".format(e.errno, e.strerror))
		except (api_v5.OneDriveInteractionError, api_v5.ProtocolError) as e:
			print("OneDrive API error.")
		SCANNER_SEMA.release()
	
	def run(self):
		self.ls()
		self.pre_merge()
		self.merge()
		self.post_merge()
	
	def pre_merge(self):
		# if remote repo has a dir that does not exist locally
		# make it and start merging
		self._ent_list = []
		if not os.path.exists(self._localPath):
			try:
				os.mkdir(self._localPath)
			except OSError as exc:
					if exc.errno == errno.EEXIST and os.path.isdir(self._localPath):
						pass
		else:
			self._ent_list = resolve_CaseConflict(self._localPath)
	
	# recursively merge the remote files and dirs into local repo
	def merge(self):
		if self._raw_log != None and self._raw_log != []:
			for entry in self._raw_log:
				if entry["name"] == None:
					continue
				if "exclude" in CONF and re.match(CONF["exclude"], entry["name"]):
					print("Remote file " + self._remotePath + "/" + entry["name"] + " is excluded.")
					continue
				self.checkout(entry)
	
	# checkout one entry, either a dir or a file, from the log
	def checkout(self, entry):
		isExistent = os.path.exists(self._localPath + "/" + entry["name"])
		if isExistent:
			del self._ent_list[self._ent_list.index(entry["name"])]
		
		localPath = self._localPath + "/" + entry["name"]
		
		if entry["type"] in "file|photo|audio|video":
			if isExistent:
				# assert for now
				assert os.path.isfile(localPath)
				local_mtime = os.stat(localPath).st_mtime
				remote_mtime = timegm(parser.parse(entry["client_updated_time"]).utctimetuple())
				
				if local_mtime == remote_mtime:
					print(self.getName() + ": " + localPath + " wasn't changed.")
					return
				elif local_mtime > remote_mtime:
					print(self.getName() + ": Local file \"" + self._localPath + "/" + entry["name"] + "\" is newer.")
					localPath_new = localPath + " (NEWER_" + str(local_mtime) + ")"
					os.rename(localPath, localPath_new)
					TASK_QUEUE.put(Task("get", localPath, self._remotePath + "/" + entry["name"], entry["client_updated_time"]))
					TASK_QUEUE.put(Task("put", localPath_new, self._remotePath + " (" + str(local_mtime) + ")"))
				else:
					print(self.getName() + ": Local file \"" + self._localPath + "/" + entry["name"] + "\" is older.")
					localPath_new = localPath + " (OLDER_" + str(local_mtime) + ")"
					os.rename(localPath, localPath_new)
					TASK_QUEUE.put(Task("get", localPath, self._remotePath + "/" + entry["name"], entry["client_updated_time"]))
					TASK_QUEUE.put(Task("put", localPath_new, self._remotePath + " (" + str(local_mtime) + ")"))
			else:
				# if not existent, get the file to local repo
				TASK_QUEUE.put(Task("get", localPath, self._remotePath + "/" + entry["name"], entry["client_updated_time"]))
		else:
			# print(self.getName() + ": scanning dir " + self._localPath + "/" + entry["name"])
			DirScanner(localPath, self._remotePath + "/" + entry["name"]).start()
	
	# process untouched files during merge
	def post_merge(self):
		# there is untouched item in current dir
		if self._ent_list != []:
			print(self.getName() + ": The following items are untouched yet:\n" + str(self._ent_list))
			
			for entry in self._ent_list:
				# assume to upload all of them
				# if it is a file
				if CONF["exclude"] != "" and re.match(CONF["exclude"], entry):
					print(self.getName() + ": " + entry + " is a pattern that is excluded.")
				elif os.path.isfile(self._localPath + "/" + entry):
					print(self._localPath + "/" + entry + " is an untouched file.")
					TASK_QUEUE.put(Task("put", self._localPath + "/" + entry, self._remotePath))
				else:	# a dir
					print(self._localPath + "/" + entry + " is an untouched dir.")
					TASK_QUEUE.put(Task("mkdir", self._localPath + "/" + entry, self._remotePath + "/" + entry))
		
		print(self.getName() + ": done.")
		# new logs should get from recent list

# LocalMonitor runs inotifywait component and parses the log
# when an event is issued, parse it and add work to the task queue.
class LocalMonitor(threading.Thread):
	MONITOR_SLEEP_INTERVAL = 2 # in seconds
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self.rootPath = CONF["rootPath"]
	
	def handle(self, logItem):
		print "local_mon: received a task: " + str(logItem)
		dir = logItem[0]
		event = logItem[1]
		object = logItem[2]
		
		if "MOVED_TO" in event:
			TASK_QUEUE.put(Task("put", dir + object, dir.replace(self.rootPath, "")))
		elif "MOVED_FROM" in event:
			TASK_QUEUE.put(Task("rm", "", dir.replace(self.rootPath, "") + object))
		elif "DELETE" in event:
			TASK_QUEUE.put(Task("rm", "", dir.replace(self.rootPath, "") + object))
		elif "CLOSE_WRITE" in event:
			TASK_QUEUE.put(Task("put", dir + object, dir.replace(self.rootPath, "")))
	
	def run(self):
		if "exclude" in CONF:
			exclude_args = ["--exclude", CONF["exclude"]]
		else:
			exclude_args = []
		subp = subprocess.Popen(['inotifywait', '-e', 'unmount,close_write,delete,move', '-cmr', self.rootPath] + exclude_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while True:
			# I think stdout buffer is fine for now
			if EVENT_STOP.is_set():
				subp.terminate()
				break
			line = subp.stdout.readline()
			if line == "":
				time.sleep(self.MONITOR_SLEEP_INTERVAL)
			elif line[0] == "/":
				line = line.rstrip()
				csv_entry = csv.reader(StringIO.StringIO(line))
				for x in csv_entry:
					self.handle(x)
			else:
				print "Local_mon: >>>" + line
		
# RemoteMonitor periodically fetches the most recent changes from OneDrive remote repo
# if there are unlocalized changes, generate the tasks
# But how to prevent it from adding duplicate tasks to LocalMonitor?
# How does it know the new changes is just made by TaskWorker?
class RemoteMonitor(threading.Thread):
	PULL_INTERVAL = 2 # in seconds
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self.rootPath = CONF["rootPath"]
	
	def run(self):
		pass

class Waiter(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
	
	def run(self):
		while not SCANNER_QUEUE.empty():
			t = SCANNER_QUEUE.get()
			SCANNER_QUEUE.task_done()
			t.join()
			del t
		
		TASK_QUEUE.join()
		
		LocalMonitor().start()
		RemoteMonitor().start()
		
		gc.collect()
		
		print "Waiter quit."
