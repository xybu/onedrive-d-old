#!/usr/bin/python

import sys, os, subprocess, yaml

# can be removed in production code
import pprint

cli_name = "skydrive_cli"

class FolderEntry:
	_raw_log = ""
	def __init__(self, path, log):
		self._raw_log = log
	
	def print_raw(self):
		mypprint(self._raw_log)
		print "\n"
	
	def get_log(self):
		# sp = subprocess.Popen(['skydrive-cli', 'ls', '--objects', self.path + self.dirname], stdout=subprocess.PIPE)
		# log = sp.communicate()[0]
		# save log dump to settings folder
		#if self.path == "" and self.dirname == "":
		#	logPath = "root.log"
		#else:
		#	logPath = self.path.replace("/", "_") + self.dirname.replace("/", "_") + ".log"
		fLog = open(os.path.expanduser("~/.onedrive/" + logPath), "w");
		fLog.write(log)
		fLog.close()
		return log

def mypprint(dict):
	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(dict)

def stub_getLog(path):
	pass

conf_path = "./dot_onedrive" # should be ~/.onedrive

conf_file = open(os.path.expanduser(conf_path + "/user.conf"), "r")
conf = yaml.safe_load(conf_file)
# conf should be a dictionary of entries of the following
# 	conf["rootPath"] - the path for OneDrive repo
conf_file.close()

conf_rootPath = conf["rootPath"]


# rotate log
if os.path.exists(conf_path + conf["newLogPath"]):
	print "old log exists."
else:
	print "there is no old log."

# print conf_rootPath

log_file = open(os.path.expanduser(conf_path + "/root.log"), "r")
log = yaml.safe_load(log_file)
log_file.close()
	
for (i, entry) in enumerate(log):
	identities = entry["id"].split(".")
	real_type = identities[0] # file or folder
	if real_type == "folder":
		ent = FolderEntry("/", entry)
		ent.print_raw()
	else:
		pass

#rootEntry = DirectoryEntry(ONEDRIVE_ROOT_DIR, "", "")
#rootEntry.sync()
