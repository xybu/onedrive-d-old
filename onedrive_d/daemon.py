#!/usr/bin/python

import sys, os, gc
import gtk, gobject, notify2
import threading
import subprocess
import config
import components
from onedrive import api_v5

gtk.gdk.threads_init()
gobject.threads_init()

def printLog(text):
	sys.stderr.write(text + "\n")

class OneDrive_StatusIcon(gtk.StatusIcon):
	_icon = None
	
	def __init__(self, api):
		if not notify2.init('onedrive-d'):
			printLog('Failed to initialize notify2.')
			sys.exit(1)
		gtk.StatusIcon.__init__(self)
		self.API = api
		self._recent_change_lock = threading.Lock()
		self._recent_changes = []
		self._last_msg = None
		
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
		
		item_quit = gtk.MenuItem("Exit")
		item_quit.connect("activate", self.quit, "file.quit")
		menu.append(item_quit)
		
		menu.show_all()
		
		self._timer = gobject.timeout_add(1000, self.e_start_daemon)
		
		self.e_update_quota()
	
	#@profile
	def e_show_root(self, widget, event=None):
		subprocess.call(['xdg-open', config.CONF["rootPath"]])
	
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
	
	def add_recent_change_item(self, path, description):
		self._recent_change_lock.acquire()
		self._recent_changes.append([path, description])
		self._recent_change_lock.release()
	
	def show_notification_message(self, title = "OneDrive", text = None, icon = "notification-message-im", timeout = 3000):
		if text == None:
			text = ""
			changes = self.get_recent_changes()
			for item in changes:
				text = text + item[0] + item[1] + "\n"
		
		if not self._last_msg:
			self._last_msg = notify2.Notification(title, text, icon)
		else:
			self._last_msg.update(title, text, icon)
		self._last_msg.set_timeout(timeout)
		if not self._last_msg.show():
			pass
	
	def get_recent_changes(self):
		self._recent_change_lock.acquire()
		t = self._recent_changes
		self._recent_change_lock.release()
		return t
	
	def add_recent_change(self, path, prompt_msg):
		self._recent_change_lock.acquire()
		self._recent_changes.append((path, prompt_msg))
		if len(self._recent_changes) > config.MAX_RECENT_ITEMS:
			del self._recent_changes[0]
		self._recent_change_lock.release()
		self.show_notification_message()
	
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
	
	if config.CONF == None:
		subprocess.call(["onedrive-prefs"])
		config.load_conf()
	
	try:
		if config.CONF == None:
			raise ValueError()
		API = api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
		quota = API.get_quota()
		config.QUOTA["free"] = quota[0]
		config.QUOTA["total"] = quota[1]
		config.AUTHENTICATED = True
	except (ValueError, IOError, api_v5.AuthenticationError) as e:
		ret = subprocess.call(["onedrive-prefs"])
		config.load_conf()
		try:
			API = api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
			quota = API.get_quota()
			config.QUOTA["free"] = quota[0]
			config.QUOTA["total"] = quota[1]
			config.AUTHENTICATED = True
		except:
			print "OneDrive-d cannot get information from the server. Exit."
			sys.exit(1)
	
	gc.collect()
	
	if not config.AUTHENTICATED or config.CONF == None:
		print "OneDrive-d was not authenticated or properly configured. Exit."
		sys.exit(1)
	
	OneDrive_StatusIcon(API).run()

if __name__ == "__main__":
	main()
