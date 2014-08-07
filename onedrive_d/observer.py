#!/usr/bin/python3

import os
import threading
import subprocess
import config
import logger

from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk, GdkPixbuf

TRAYICON_UPDATE_INTERVAL = 5 # in seconds

class OneDrive_GtkStatusIcon(Gtk.StatusIcon):
	def __init__(self, log = None):
		
		if log != None:
			self.logger = log
		
		GObject.GObject.__init__(self)
		self.connect("activate", self.on_activate)
		self.connect("popup-menu", self.on_popup_menu)
		self.icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(os.path.dirname(__file__) + "/res/icon_256.png")
		self.set_from_pixbuf(self.icon_pixbuf)
		self.set_visible(True)
	
	def on_activate(self, icon):
		# TODO: Change to the correct path
		subprocess.call(['xdg-open', '/'])
	
	def on_popup_menu(self, icon, button, time):
		"""Display a menu to allow quitting."""
		menu = Gtk.Menu()
		
		item = Gtk.MenuItem("Visit OneDrive.com")
		item.connect("activate", self.open_browser, None)
		menu.append(item)
		
		menu.append(Gtk.SeparatorMenuItem())
		
		item = Gtk.MenuItem(label="Quit")
		item.connect("activate", Gtk.main_quit)
		menu.append(item)
		
		menu.show_all()
		menu.popup(parent_menu_shell=None,
			parent_menu_item=None,
			func=lambda a,b: Gtk.StatusIcon.position_menu(menu, icon),
			data=None,
			button=button,
			activate_time=time)
		self.logger.debug('StatusIcon popmenu got called.')
	
	def open_browser(self):
		from webbrowser import open_new
		open_new("https://onedrive.com")
	
	def update(self):
		while Gtk.events_pending():
			Gtk.main_iteration()
		self.logger.debug('StatusIcon updated once.')
		return True
	
class OneDrive_ObserverThread(threading.Thread):
	
	def __init__(self, log_path = None, log_min_level = logger.Logger.NOTSET):
		super().__init__()
		self.name = 'monitor'
		self.daemon = True
		self.logger = logger.Logger(log_path, log_min_level)
	
	def run(self):
		self.logger.debug('start running')
		self.status_icon = OneDrive_GtkStatusIcon(log = self.logger)
		GLib.timeout_add_seconds(TRAYICON_UPDATE_INTERVAL, self.status_icon.update)
		Gtk.main()
	