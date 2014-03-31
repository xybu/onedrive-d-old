#!/usr/bin/python

# Warning: Rely heavily on system time and if the timestamp is screwed there may be unwanted file deletions.

import sys, os, subprocess, yaml
import threading, Queue, time

class Task():
	def __init__(self, type, pathType, localPath, remotePath):
		self.type = type
		self.pathType = pathType
		self.localPath = localPath
		self.remotePath = remotePath
	
	def type(self):
		return self.type
	
	def pathType(self):
		return self.pathType
	
	def localPath(self):
		return self.localPath
	
	def remotePath(self):
		return self.remotePath
	
	def debug(self):
		return "type=" + self.type + " | pathType=" + self.pathType + " | localPath=" + self.localPath + " | remotePath=" + self.remotePath
	
# TaskWorker class builds the consumer threads of the task queue
class TaskWorker(threading.Thread):
	WORKER_SLEEP_INTERVAL = 2 # in seconds
	
	def __init__(self):
		threading.Thread.__init__(self)
	
	# download a file to localPath
	def get_file(self, entry):
		pass
	
	# upload a file to remotePath
	def put_file(self, entry):
		pass
	
	# remove a file from remotePath
	def rm_file(self, entry):
		pass
	
	# make a dir to remotePath
	def mk_dir(self, ent_stat):
		pass
	
	def consume(self, t):
		print self.getName() + ": executed a task: " + t.debug()
	
	def run(self):
		while True:
			if workers_signal_exit == 1:
				break
			elif taskQueue.empty():
				time.sleep(self.WORKER_SLEEP_INTERVAL)
			else:
				task = taskQueue.get()
				taskQueue.task_done()
				self.consume(task)

# DirScanner represents either a file entry or a dir entry in the OneDrive repository
# it uses a single thread to process a directory entry
class DirScanner(threading.Thread):
	_raw_log = []
	_ent_list = []
	_remotePath = ""
	_localPath = ""
	
	def __init__(self, localPath, remotePath):
		threading.Thread.__init__(self)
		self._localPath = localPath
		self._remotePath = remotePath
		print self.getName() + ": Start scanning dir " + remotePath + " (locally at \"" + localPath + "\")"
		self.ls()
	
	def ls(self):
		subp = subprocess.Popen(['skydrive-cli', 'ls', '--objects', self._remotePath], stdout=subprocess.PIPE)
		log = subp.communicate()[0]
		self._raw_log = yaml.safe_load(log)
	
	def run(self):
		threads_lock.acquire()
		threads.append(self)
		threads_lock.release()
		self.merge()
	
	# list the current dirs and files in the local repo, and in merge() upload / delete entries accordingly
	def pre_merge(self):
		# if remote repo has a dir that does not exist locally
		# make it and start merging
		if not os.path.exists(self._localPath):
			try:
				os.mkdir(self._localPath)
			except OSError as exc: 
					if exc.errno == errno.EEXIST and os.path.isdir(self._localPath):
						pass
		else:
			# if the local path exists, record what is in the local path
			self._ent_list = os.listdir(self._localPath)
	
	# recursively merge the remote files and dirs into local repo
	def merge(self):
		self.pre_merge()
		
		if self._raw_log == None:
			return
		for entry in self._raw_log:
			if os.path.exists(self._localPath + "/" + entry["name"]):
				print self.getName() + ": Oops, " + self._localPath + "/" + entry["name"] + " exists."
				# do some merge
				self.checkout(entry, True)
				# after sync-ing
				del self._ent_list[self._ent_list.index(entry["name"])] # remove the ent from untouched list
			else:
				print self.getName() + ": Wow, " + self._localPath + "/" + entry["name"] + " does not exist."
				self.checkout(entry, False)
		
		self.post_merge()
	
	# checkout one entry, either a dir or a file, from the log
	def checkout(self, entry, isExistent = False):
		if entry["type"] == "file" or entry["type"] == "photo" or entry["type"] == "audio" or entry["type"] == "video":
			print self.getName() + ": adding task to sync " + self._localPath + "/" + entry["name"]
			taskQueue.put(Task("download", "file", self._localPath + "/" + entry["name"], self._remotePath + "/" + entry["name"]))
		else:
			print self.getName() + ": scanning dir " + self._localPath + "/" + entry["name"]
			ent = DirScanner(self._localPath + "/" + entry["name"], self._remotePath + "/" + entry["name"])
			ent.start()
	
	# note: mv, cp, and del will be handled by daemon rather than this sync script
	
	# process untouched files during merge
	def post_merge(self):
		# there is untouched item in current dir
		if self._ent_list != []:
			print self.getName() + ": The following items are untouched yet:\n" + str(self._ent_list)
			for entry in self._ent_list:
				# assuming it is a file for now
				taskQueue.put(Task("upload", "file", self._localPath + "/" + entry, self._remotePath + "/" + entry))
		print self.getName() + ": done."
		# new logs should get from recent list
	
	# print the internal storage
	def debug(self):
		print "localPath: " + self._localPath + ""
		print "remotePath: " + self._remotePath + ""
		print self._raw_log
		print "\n"
		print self._ent_list
		print "\n"

# Monitor runs inotifywait component and parses the log
# when an event is issued, parse it and add work to the task queue.
class Monitor(threading.Thread):
	def __init__(self, rootPath):
		threading.Thread.__init__(self)
	
	def run(self):
		pass
		
CONF_PATH = "~/.onedrive"

f = open(os.path.expanduser(CONF_PATH + "/user.conf"), "r")
CONF = yaml.safe_load(f)
f.close()

threads = []
threads_lock = threading.Lock()

taskQueue = Queue.Queue()
workers_signal_exit = 0

rootThread = DirScanner(CONF["rootPath"], "")
rootThread.start()

numOfWorkers = 4

for i in range(numOfWorkers):
	w = TaskWorker()
	w.start()

for t in threads:
    t.join()

taskQueue.join()

workers_signal_exit = 1

print "Main: all done."

#print "All threads are done."
#print threads

# Main thread then should create monitor and let workers continually consume the queue
