#!/usr/bin/python

from skydrive import api_v5
import subprocess
import gtk
import pynotify

# Left click: show local repository
# Right click: show menu
#	menu items: 
#		launch onedrive.com
#		quota
#		recent changes
#		status
#		exit
class OneDrive_StatusIcon(gtk.StatusIcon):
	@profile
	def __init__(self, api, rootPath):
		gtk.StatusIcon.__init__(self)
		self._rootPath = rootPath
		self._api = api
		self.set_from_file("./res/icon_256.png")
		self.set_tooltip('onedrive-d')
		self.connect("activate", self.show_local_repo)
		self.connect('popup-menu', self.icon_clicked)
		self.set_visible(True)
		
		self.menu = menu = gtk.Menu()
		
		open_repo_item = gtk.MenuItem("Open OneDrive directory")
		open_repo_item.connect("activate", self.show_local_repo, "Open OneDrive directory")
		menu.append(open_repo_item)
		
		menu.append(gtk.SeparatorMenuItem())
		
		self.quota_item = quota_item = gtk.MenuItem("Loading quota...");
		quota_item.connect("activate", self.update_quota, None)
		menu.append(quota_item)
		# menu.append(gtk.SeparatorMenuItem())
		
		menu_website = gtk.MenuItem("Visit OneDrive.com")
		menu_website.connect("activate", self.show_website, None)
		menu.append(menu_website)
		
		menu.append(gtk.SeparatorMenuItem())
		
		menu_settings = gtk.MenuItem("Settings")
		menu_settings.connect("activate", self.show_settings, None)
		menu.append(menu_settings)
		
		menu_test = gtk.MenuItem("test item")
		menu_test.connect("activate", self.show_notification, None)
		menu.append(menu_test)
		
		menu_about = gtk.MenuItem("About")
		menu_about.connect("activate", self.show_about, None)
		menu.append(menu_about)
		
		menu_quit = gtk.MenuItem("Exit")
		menu_quit.connect("activate", self.quit, "file.quit")
		menu.append(menu_quit)
		
		menu.show_all()
		self.update_quota()
	
	@profile
	def show_local_repo(self, widget, event=None):
		subprocess.check_call(['gnome-open', self._rootPath, ''])
	
	@profile
	def show_settings(self, widget, event=None):
		OneDrive_SettingsWindow()	
	
	@profile
	def icon_clicked(self, status, button, time):
		self.menu.popup(None, None, None, button, time)
	
	@profile
	def update_quota(self, widget=None, event=None):
		quota = self._api.get_quota()
		usedPercentage = float(quota[0]) / quota[1] * 100
		totalSize = "%.2fGiB" % self.toGigabyte(quota[1])
		self.quota_item.set_label("%.1f%% of %s Free" % (usedPercentage, totalSize))
		self.quota_item.set_sensitive(False)
	
	@profile
	def show_about(self, widget=None, event=None):
		pass
	
	@profile
	def show_website(self, widget=None, event=None):
		import webbrowser
		webbrowser.open_new("https://onedrive.com")
	
	@profile
	def show_notification(self, widget=None, event=None):
		OneDrive_Notification().show()
	
	@profile
	def toGigabyte(self, size):
		return float(size) / 1073741824
	
	def run(self):
		gtk.main()
	
	@profile
	def quit(self, widget, event=None):
		gtk.main_quit()
	
# set-up packages?
class OneDrive_SetupWindow(gtk.Window):
	pass

# authorization panel
# local repository path
class OneDrive_SettingsWindow(gtk.Window):
	def __init__(self):
		super(OneDrive_SettingsWindow, self).__init__()
		
		self.set_title("Settings")
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_default_size(640, 600)
		self.set_geometry_hints(min_width=640, min_height=600)
		self.set_icon_from_file("./res/icon_256.png")
		self.connect("destroy", self.window_destroy)
		
		#box = gtk.VBox()
		#button = gtk.Button("Test Button")
		#box.pack_start(button, False)
		#self.add(box)
		
		text = gtk.Entry()
		self.add(text)
		
		self.show_all()
		
	def window_destroy(self,widget):
		self.hide_all()

# list the log
class OneDrive_MonitorWindow(gtk.Window):
	pass

# show the about info and possible updates
class OneDrive_AboutWindow(gtk.Window):
	pass

# issue a notification
class OneDrive_Notification():
	def __init__(self):
		if not pynotify.init ("icon-summary-body"):
			return
		self.n = pynotify.Notification ("Cole Raby",
				   "Hey pal, what's up with the party "
				   "next weekend? Will you join me "
				   "and Anna?",
				   "notification-message-im")
		self.n.set_timeout(3000)
	
	def show(self):
		self.n.show()
		del self

if __name__ == "__main__":
	import yaml, os
	f = open(os.path.expanduser("~/.onedrive/user.conf"), "r")
	CONF = yaml.safe_load(f)
	f.close()
	api_o = api_v5.PersistentSkyDriveAPI.from_conf("~/.lcrc")
	OneDrive_StatusIcon(rootPath = CONF["rootPath"], api = api_o).run()
