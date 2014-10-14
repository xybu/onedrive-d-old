#!/usr/bin/python3

'''
A PyGI based observer that updates status icon and 
shows notification messages.
'''

import os
import time
import subprocess
import threading
import config
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk, GdkPixbuf

TRAYICON_UPDATE_INTERVAL = 2 # in seconds
RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))

class OneDrive_GtkWorker(threading.Thread):
	def __init__(self):
		super().__init__()
	
	def run(self):
		pass

class OneDrive_Observer(Gtk.StatusIcon):
	
	def __init__(self):
		GObject.GObject.__init__(self)
		self.name = 'gtk'
		self.connect("activate", self.on_activate)
		self.connect("popup-menu", self.on_popup_menu)
		self.icon_busy = GdkPixbuf.Pixbuf.new_from_file(RESOURCE_PATH + "/res/icon_256.png")
		self.icon_idle = GdkPixbuf.Pixbuf.new_from_file(RESOURCE_PATH + "/res/icon_256_idle.png")
		self.set_from_pixbuf(self.icon_idle)
		self.set_visible(True)
	
	def notify(self):
		config.log.info('I got notified of something.')
	
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
		item.connect("activate", self.stop)
		menu.append(item)
		
		menu.show_all()
		menu.popup(parent_menu_shell=None,
			parent_menu_item=None,
			func=lambda a,b: Gtk.StatusIcon.position_menu(menu, icon),
			data=None,
			button=button,
			activate_time=time)
		config.log.debug('StatusIcon popmenu got called.')
	
	def open_browser(self):
		from webbrowser import open_new
		open_new("https://onedrive.com")
	
	def update(self):
		self.set_from_pixbuf(self.icon_busy)
		# self.set_visible(True)
		while Gtk.events_pending():
			Gtk.main_iteration()
		time.sleep(1)
		config.log.debug('StatusIcon updated once.')
		self.set_from_pixbuf(self.icon_idle)
		# self.set_visible(True)
		return True
	
	def run(self):
		GLib.timeout_add_seconds(TRAYICON_UPDATE_INTERVAL, self.update)
		Gtk.main()
	
	def stop(self, widget = None):
		Gtk.main_quit()

OneDrive_Observer().run()