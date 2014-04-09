#!/usr/bin/python

from skydrive import api_v5
import os
import subprocess
import gtk
import pynotify

# Left click: show local repository
# Right click: show menu
class OneDrive_StatusIcon(gtk.StatusIcon):
	last_notification = None
	recent_changes = []
	PYNOTIFY_INITED = False
	_icon = None
	
	#@profile
	def __init__(self, api, rootPath):
		gtk.StatusIcon.__init__(self)
		
		self._rootPath = rootPath
		self._icon_pixbuf = gtk.gdk.pixbuf_new_from_file("./res/icon_256.png")
		self.set_from_pixbuf(self._icon_pixbuf)
		self.set_tooltip('onedrive-d')
		self.connect("activate", self.e_show_root)
		self.connect('popup-menu', self.e_click_icon)
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
		item_quota.connect("activate", self.e_update_quota, None)
		menu.append(item_quota)
		
		item_web = gtk.MenuItem("Visit OneDrive.com")
		item_web.connect("activate", self.e_show_web, None)
		menu.append(item_web)
		
		menu.append(gtk.SeparatorMenuItem())
		
		item_settings = gtk.MenuItem("Settings")
		item_settings.connect("activate", self.e_show_settings, None)
		menu.append(item_settings)
		
		item_test = gtk.MenuItem("test item")
		item_test.connect("activate", self.e_show_notification, None)
		menu.append(item_test)
		
		item_quit = gtk.MenuItem("Exit")
		item_quit.connect("activate", self.quit, "file.quit")
		menu.append(item_quit)
		
		menu.show_all()
		self.e_update_quota()
	
	#@profile
	def e_show_root(self, widget, event=None):
		subprocess.check_call(['gnome-open', self._rootPath, ''])
	
	#@profile
	def e_show_settings(self, widget, event=None):
		OneDrive_SettingsWindow(self._icon_pixbuf)
	
	def e_show_monitor(self, widget, event=None):
		pass
	
	#@profile
	def e_click_icon(self, status, button, time):
		self.menu.popup(None, None, None, button, time)
	
	#@profile
	def e_show_web(self, widget=None, event=None):
		from webbrowser import open_new
		open_new("https://onedrive.com")
	
	#@profile
	def e_update_quota(self, widget=None, event=None):
		quota = api.get_quota()
		usedPercentage = float(quota[0]) / quota[1] * 100
		totalSize = "%.2fGiB" % (float(quota[1]) / 1073741824)
		self.item_quota.set_label("%.1f%% of %s Free" % (usedPercentage, totalSize))
		self.item_quota.set_sensitive(False)
	
	#@profile
	def e_show_notification(self, widget=None, event=None):
		self.add_notification("Title", "This is a test message!")
	
	#@profile
	def add_notification(self, title, text, icon = "notification-message-im", timeout = 2000):
		if not self.PYNOTIFY_INITED and not pynotify.init ("icon-summary-body"):
			return
		self.last_notification = pynotify.Notification(title, text, icon)
		self.last_notification.set_timeout(timeout)
		self.last_notification.show()
	
	def add_recent_change(self, path):
		submenu = self.item_recent.get_submenu()
		if submenu == None:
			pass
		pass
	
	def run(self):
		gtk.main()
	
	def quit(self, widget, event=None):
		gtk.main_quit()

# authorization panel
# local repository path
class OneDrive_SettingsWindow(gtk.Window):
	#@profile
	def __init__(self, pixbuf):
		super(OneDrive_SettingsWindow, self).__init__()
		
		self.set_title("Settings")
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_default_size(640, 600)
		self.set_geometry_hints(min_width=640, min_height=600)
		#self.set_icon_from_file("./res/icon_256.png")
		self.set_icon(pixbuf)
		#self.connect("destroy", self.window_destroy)
		
		#box = gtk.VBox()
		#button = gtk.Button("Test Button")
		#box.pack_start(button, False)
		#self.add(box)
		
		text = gtk.Entry()
		self.add(text)
		
		self.show_all()
	
	#@profile
	#def window_destroy(self, widget):
	#	# self.hide_all()
	#	del self

# list the log
class OneDrive_MonitorWindow(gtk.Window):
	pass

#@profile
def main():
	import yaml
	f = open(os.path.expanduser("~/.onedrive/user.conf"), "r")
	CONF = yaml.safe_load(f)
	f.close()
	api_o = api_v5.PersistentSkyDriveAPI.from_conf("~/.lcrc")
	OneDrive_StatusIcon(api_o, CONF["rootPath"]).run()

if __name__ == "__main__":
	main()
