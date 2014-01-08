import sys, os
import yaml
import subprocess
import calendar
from dateutil import parser

class FileEntry:
	def __init__(self, localroot, remotePath, filename, size, mtime):
		if localroot != "" and localroot[-1] != "/":
			localroot = localroot + "/"
		if remotePath != "" and remotePath[-1] != "/":
			remotePath = remotePath + "/"
		self.localroot = localroot
		self.path = remotePath
		self.filename = filename
		self.size = size
		#sample: 2013-10-31T02:58:31+0000
		self.mtime = calendar.timegm(parser.parse(mtime).utctimetuple())
	
	def sync(self):
		fPath = self.localroot + self.path + self.filename
		if os.path.exists(fPath):
			if os.path.isfile(fPath):
				fMtime = os.stat(fPath).st_mtime
				#print "File \"" + fPath + "\" has fMtime " + str(os.stat(fPath).st_mtime)
				#print "File \"" + fPath + "\" has mtime " + str(self.mtime)
				if fMtime > self.mtime:
					print "Local file \""+fPath+"\" is newer. Upload it..."
					self.upload()
				elif fMtime < self.mtime:
					print "Local file \""+fPath+"\" is older. Download it..."
					self.download()
				else:
					print fPath + " wasn't changed. Skip it."
			else:
				print fPath + " is not a file!"
		else:
			#TODO: FILE DELETION?
			print fPath + " does not exist. Download it."
			self.download()
	
	def upload(self):
		print "Uploading file \" " + self.localroot + self.path + self.filename + "\""
		upProc = subprocess.Popen(['skydrive-cli', 'put', self.path + self.filename, self.path], cwd="" + self.localroot + "", stdout=subprocess.PIPE)
		result = upProc.communicate()[0]
		print result
	
	def download(self):
		print "Writing to file \" " + self.localroot + self.path + self.filename + "\""
		print "Downloading file \"" + self.path + self.filename + "\""
		f = open(self.localroot + self.path + self.filename, "w")
		downProc = subprocess.call(['skydrive-cli', 'get', self.path + self.filename], stdout=f)
		#os.waitpid(downProc.pid, 0)
		f.close()
		os.utime(self.localroot + self.path + self.filename, (self.mtime, self.mtime))

class DirectoryEntry:
	def __init__(self, root, path, dirname, mtime = ""):
		if root != "" and root[-1] != "/":
			root = root + "/"
		if path != "" and path[-1] != "/":
			path = path + "/"
		if dirname != "" and dirname[-1] != "/":
			dirname = dirname + "/"
		self.localroot = root
		self.path = path
		self.dirname = dirname
		if mtime != "":
			self.mtime = calendar.timegm(parser.parse(mtime).utctimetuple())
	
	def getLog(self):
		sp = subprocess.Popen(['skydrive-cli', 'ls', '--objects', self.path + self.dirname], stdout=subprocess.PIPE)
		log = sp.communicate()[0]
		#save log dump to settings folder
		if self.path == "" and self.dirname == "":
			logPath = "root.log"
		else:
			logPath = self.path.replace("/", "_") + self.dirname.replace("/", "_") + ".log"
		fLog = open(os.path.expanduser("~/.skydrive/" + logPath), "w");
		fLog.write(log)
		fLog.close()
		return log
	
	def sync(self):
		log = self.getLog()
		if log == "":
			return
		
		logMap = yaml.safe_load(log)

		for entry in logMap:
			if entry["type"] == "file" or entry["type"] == "photo" or entry["type"] == "audio" or entry["type"] == "video":
				fEntry = FileEntry(self.localroot, self.path + self.dirname, entry["name"], entry["size"], entry["client_updated_time"])
				fEntry.sync()
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
SKYDRIVE_ROOT_DIR = settingsMap["rootPath"] + "/"

rootEntry = DirectoryEntry(SKYDRIVE_ROOT_DIR, "", "")
rootEntry.sync()
