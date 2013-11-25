import sys, os
import yaml
import subprocess
import calendar
from dateutil import parser

class FileEntry:
	def __init__(self, localroot, remotePath, filename, size, ctime, mtime):
		if localroot != "" and localroot[-1] != "/":
			localroot = localroot + "/"
		if remotePath != "" and remotePath[-1] != "/":
			remotePath = remotePath + "/"
		self.localroot = localroot
		self.path = remotePath
		self.filename = filename
		self.size = size
		#sample: 2013-10-31T02:58:31+0000
		self.ctime = calendar.timegm(parser.parse(ctime).utctimetuple())
		self.mtime = calendar.timegm(parser.parse(mtime).utctimetuple())
		
	def download(self):
		print "Writing to file \" " + self.localroot + self.path + self.filename + "\""
		f = open(self.localroot + self.path + self.filename, "w")
		print "Downloading from file \"" + self.path + self.filename + "\""
		downProc = subprocess.Popen(['skydrive-cli', 'get', self.path + self.filename], stdout=f)
		f.close()
		os.utime(self.localroot + self.path + self.filename, (self.ctime, self.mtime))

class DirectoryEntry:
	def __init__(self, root, path, dirname, ctime = "", mtime = ""):
		if root != "" and root[-1] != "/":
			root = root + "/"
		if path != "" and path[-1] != "/":
			path = path + "/"
		if dirname != "" and dirname[-1] != "/":
			dirname = dirname + "/"
		self.localroot = root
		self.path = path
		self.dirname = dirname
		if ctime != "":
			self.ctime = calendar.timegm(parser.parse(ctime).utctimetuple())
		if mtime != "":
			self.mtime = calendar.timegm(parser.parse(mtime).utctimetuple())
	
	def getLog(self):
		sp = subprocess.Popen(['skydrive-cli', 'ls', '--objects', self.path + self.dirname], stdout=subprocess.PIPE)
		log = sp.communicate()[0]
		#print log
		return log
	
	def sync(self):
		log = self.getLog()
		if log == "":
			return
		
		logMap = yaml.safe_load(log)

		for entry in logMap:
			if entry["type"] == "file" or entry["type"] == "photo" or entry["type"] == "audio":
				fEntry = FileEntry(self.localroot, self.path + self.dirname, entry["name"], entry["size"], entry["created_time"], entry["updated_time"])
				fEntry.download()
			elif entry["type"] == "folder" or entry["type"] == "album":
				print entry["name"] + " is a folder."
				if not os.path.exists(self.localroot + self.path + self.dirname + entry["name"]):
					print "mkdir: " + self.localroot + self.path + self.dirname + entry["name"]
					print self.localroot + self.path + self.dirname + entry["name"] + " does not exist. make it."
					os.mkdir(self.localroot + self.path + self.dirname + entry["name"])
				dEntry = DirectoryEntry(self.localroot, self.path + self.dirname, entry["name"])
				dEntry.sync()
			else:
				print entry["name"] + " is a " + entry["type"] + "."

settingsFile = open(os.path.expanduser("~/.skydrive/user.conf"), "r");
settingsMap = yaml.safe_load(settingsFile)
settingsFile.close()
SKYDRIVE_ROOT_DIR = settingsMap["settings"]["root"] + "/"

rootEntry = DirectoryEntry(SKYDRIVE_ROOT_DIR, "", "")
rootEntry.sync()
