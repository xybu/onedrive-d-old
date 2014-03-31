#!/usr/bin/python

# Perform a deep synchronization and handle all file changes
# After running the script local OneDrive repo and remote OneDrive repo should be in sync
# Warning: Rely heavily on system time

import sys, os, subprocess, yaml

class DirectoryEntry:
	_raw_log = []
	_ent_list = []
	_remotePath = ""
	_localPath = ""
	
	def __init__(self, localPath, remotePath):
		self.localPath = localPath
		self.remotePath = remotePath
		self.ls()
	
	def ls(self):
		subp = subprocess.Popen(['skydrive-cli', 'ls', '--objects', self._remotePath], stdout=subprocess.PIPE)
		log = subp.communicate()[0]
		self._raw_log = yaml.safe_load(log)
	
	# list the current dirs and files in the local repo, and upload / delete entries accordingly
	def pre_sync(self):
		# if remote repo has a dir that does not exist locally
		# make it and start sync
		if not os.path.exists(localPath):
			try:
				os.mkdir(localPath)
			except OSError as exc: 
					if exc.errno == errno.EEXIST and os.path.isdir(path):
						pass
		else:
			# if the local path exists, record what is in the local path
			self._ent_list = os.listdir(localPath)
	
	# recursively do sync
	def sync(self):
		self.pre_sync()
		
		if log == None:
			return
		for entry in log:
			if entry["type"] == "file":
				pass
			else:
				pass
		self.post_sync()
	
	# process untouched files during sync
	def post_sync(self):
		# there is untouched item in current dir
		if self._ent_list != []:
			pass
	
	def _debug(self):
		print "localPath: " + self._localPath + "\n"
		print "remotePath: " + self._remotePath + "\n"
		print self._raw_log
		print "\n"
		print self._ent_list
		print "\n"
	
CONF_PATH = "./dot_onedrive"	# should be ~/.onedrive in Linux

f = open(os.path.expanduser(CONF_PATH + "/user.conf"), "r")
CONF = yaml.safe_load(f)
f.close()

rootDir = DirectoryEntry(CONF["rootPath"], "").sync()
