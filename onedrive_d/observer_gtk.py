#!/usr/bin/python3

'''
A PyGI based observer that updates status icon and 
shows notification messages.
'''

import os
import subprocess
import threading
import config
import logger
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk, GdkPixbuf

TRAYICON_UPDATE_INTERVAL = 20 # in seconds

observer_logger = logger.Logger(config.LOGGING_FILE_PATH, config.LOGGING_MIN_LEVEL)

class OneDrive_Observer(Gtk.StatusIcon):
	
	def __init__(self, event_lock):
		GObject.GObject.__init__(self)
		self.name = 'gtk'
		self.event_lock = event_lock
		self.connect("activate", self.on_activate)
		self.connect("popup-menu", self.on_popup_menu)
		self.icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(os.path.dirname(__file__) + "/res/icon_256.png")
		self.set_from_pixbuf(self.icon_pixbuf)
		self.set_visible(True)
	
	def set_daemon(self, obj):
		self.daemon_thread = obj
	
	def handle_event(self, event_id, event_args):
		self.handler.handle_event(event_id, event_args)
	
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
		observer_logger.debug('StatusIcon popmenu got called.')
	
	def open_browser(self):
		from webbrowser import open_new
		open_new("https://onedrive.com")
	
	def update(self):
		self.event_lock.set()
		while Gtk.events_pending():
			Gtk.main_iteration()
		observer_logger.debug('StatusIcon updated once.')
		return True
	
	def run(self):
		GLib.timeout_add_seconds(TRAYICON_UPDATE_INTERVAL, self.update)
		Gtk.main()
	
	def stop(self, widget = None):
		self.daemon_thread.stop()
		self.event_lock.set()
		self.daemon_thread.join()
		Gtk.main_quit()