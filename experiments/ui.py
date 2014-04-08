#!/usr/bin/python

import sys, os, subprocess, yaml
import gtk

class SettingsWindow(gtk.Window):
	def __init__(self):
		super(SettingsWindow, self).__init__()
		
		self.set_title("Settings | OneDrive Daemon")
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
	
class TrayIcon(gtk.StatusIcon):
	def __init__(self, rootPath):
		gtk.StatusIcon.__init__(self)
		self._rootPath = rootPath
		
		self.set_from_file("./res/icon_256.png")
		self.set_tooltip('onedrive-d monitor')
		self.set_visible(True)

		self.menu = menu = gtk.Menu()
		
		open_repo_item = gtk.MenuItem("Open OneDrive directory")
		open_repo_item.connect("activate", self.show_local_repo, "Open OneDrive directory")
		menu.append(open_repo_item)
		
		window_item = gtk.MenuItem("Settings")
		window_item.connect("activate", self.show_settings_window, "Settings")
		menu.append(window_item)
		
		quit_item = gtk.MenuItem("Exit")
		quit_item.connect("activate", self.quit, "file.quit")
		menu.append(quit_item)
		menu.show_all()

		self.connect("activate", self.show_local_repo)
		self.connect('popup-menu', self.icon_clicked)
	
	def show_local_repo(self, widget, event=None):
		subprocess.check_call(['gnome-open', self._rootPath, ''])
	
	def show_settings_window(self, widget, event=None):
		SettingsWindow()	

	def icon_clicked(self, status, button, time):
		self.menu.popup(None, None, None, button, time)

	def quit(self, widget, event=None):
		sys.exit(0)

if __name__ == "__main__":
	f = open(os.path.expanduser("~/.onedrive/user.conf"), "r")
	CONF = yaml.safe_load(f)
	f.close()
	
	TrayIcon(CONF["rootPath"])
	gtk.main()
