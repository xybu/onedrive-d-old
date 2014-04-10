#!/usr/bin/python

import sys
import os
import gc
import gtk
import gobject
import pynotify
import threading
import subprocess
import config
import components
import onedrive

gtk.gdk.threads_init()
gobject.threads_init()

def printLog(text):
	sys.stderr.write(text + "\n")

class OneDrive_StatusIcon(gtk.StatusIcon):
	_last_message = None
	_recent_changes = []
	_pynotify_flag = False
	_icon = None
	
	def __init__(self, api):
		gtk.StatusIcon.__init__(self)
		self.API = api
		self._recent_change_lock = threading.Lock()
		
		self._icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.dirname(__file__) + "/res/icon_256.png")
		
		self.set_from_pixbuf(self._icon_pixbuf)
		self.set_tooltip('onedrive-d')
		self.connect("activate", self.e_show_root)
		self.connect("popup-menu", self.e_click_icon)
		self.set_visible(True)
		
		self.menu = menu = gtk.Menu()
		
		item_open = gtk.MenuItem("Open OneDrive directory")
		item_open.connect("activate", self.e_show_root, "Open OneDrive directory")
		menu.append(item_open)
		
		self.item_recent = item_recent = gtk.MenuItem("Recent changes")
		item_recent_sub = gtk.Menu()
		item_recent_sub_all = gtk.MenuItem("All changes")
		item_recent_sub_all.connect("activate", self.e_show_monitor, None)
		item_recent_sub.append(item_recent_sub_all)
		item_recent_sub.append(gtk.SeparatorMenuItem())
		item_recent.set_submenu(item_recent_sub)
		menu.append(item_recent)
		
		menu.append(gtk.SeparatorMenuItem())
		
		self.item_quota = item_quota = gtk.MenuItem("Loading quota...");
		# item_quota.connect("activate", self.e_update_quota, None)
		menu.append(item_quota)
		
		item_web = gtk.MenuItem("Visit OneDrive.com")
		item_web.connect("activate", self.e_show_web, None)
		menu.append(item_web)
		
		menu.append(gtk.SeparatorMenuItem())
		
		item_settings = gtk.MenuItem("Settings")
		item_settings.connect("activate", self.e_show_settings, None)
		menu.append(item_settings)
		
		item_test = gtk.MenuItem("test item")
		item_test.connect("activate", self.e_show_message, None)
		menu.append(item_test)
		
		item_quit = gtk.MenuItem("Exit")
		item_quit.connect("activate", self.quit, "file.quit")
		menu.append(item_quit)
		
		menu.show_all()
		
		self._timer = gobject.timeout_add(1000, self.e_start_daemon)
		
		self.e_update_quota()
	
	#@profile
	def e_show_root(self, widget, event=None):
		subprocess.check_call(['gnome-open', config.CONF["rootPath"], ''])
	
	#@profile
	def e_show_settings(self, widget, event=None):
		# OneDrive_SettingsWindow(self._icon_pixbuf)
		pass
	
	def e_show_monitor(self, widget, event=None):
		pass
	
	def e_start_daemon(self):
		
		gobject.source_remove(self._timer)
		components.API = self.API
		components.AGENT = self
		
		for i in range(config.NUM_OF_WORKERS):
			w = components.TaskWorker()
			config.WORKER_THREADS.append(w)
			w.start()
		
		components.DirScanner(config.CONF["rootPath"], "").start()
		components.Waiter().start()
		
		print "main: All threads should have started."
			
	def e_click_icon(self, status, button, time):
		self.menu.popup(None, None, None, button, time)
	
	def e_show_web(self, widget=None, event=None):
		from webbrowser import open_new
		open_new("https://onedrive.com")
	
	def e_update_quota(self, widget=None, event=None):
		quota = config.QUOTA
		usedPercentage = float(quota["free"]) / quota["total"] * 100
		totalSize = "%.2fGiB" % (float(quota["total"]) / 1073741824)
		self.item_quota.set_label("%.1f%% of %s Free" % (usedPercentage, totalSize))
		self.item_quota.set_sensitive(False)
	
	def e_show_message(self, widget=None, event=None):
		self.add_message("Title", "This is a test message!")
	
	def add_recent_change_item(self, path, description):
		self._recent_change_lock.acquire()
		self._recent_changes.append([path, description])
		self._recent_change_lock.release()
	
	def add_message(self, title, text, icon = "notification-message-im", timeout = 4000):
		if not self._pynotify_flag and not pynotify.init ("icon-summary-body"):
			return
		self.last_message = pynotify.Notification(title, text, icon)
		self.last_message.set_timeout(timeout)
		self.last_message.show()
	
	def add_recent_change(self, path):
		submenu = self.item_recent.get_submenu()
		if submenu == None:
			pass
		pass
	
	def run(self):
		gtk.main()
	
	def quit(self, widget, event=None):
		printLog('main: time to exit')
		config.EVENT_STOP.set()
		for w in config.WORKER_THREADS:
			w.join()
		gtk.main_quit()

def main():
	global API	
	
	gc.enable()
	try:
		API = onedrive.api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
		quota = API.get_quota()
		config.QUOTA["free"] = quota[0]
		config.QUOTA["total"] = quota[1]
		config.AUTHENTICATED = True
	except (IOError, onedrive.api_v5.AuthenticationError) as e:
		subp = subprocess.Popen(["onedrive-auth"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		ret = subp.communicate()
		print ret[0]
		print ret[1]
		if ret[0] != None and "succeeded" in ret[0]:
			try:
				API = onedrive.api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
				quota = API.get_quota()
				config.QUOTA["free"] = quota[0]
				config.QUOTA["total"] = quota[1]
				config.AUTHENTICATED = True
			except:
				print "OneDrive-d cannot get information from the server. Exit."
				sys.exit(1)
		else:
			print "The authentication process failed. Exit."
			sys.exit(1)
		gc.collect()
	
	if not config.AUTHENTICATED:
		print "OneDrive-d was not authenticated. Exit."
		sys.exit(1)
	
	OneDrive_StatusIcon(API).run()

if __name__ == "__main__":
	main()
