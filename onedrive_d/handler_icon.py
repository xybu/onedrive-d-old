#!/usr/bin/python3

'''
A PyGI based handler that updates status icon and 
shows notification messages.

handler_name: gtk
'''

import os
import subprocess
import config
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk, GdkPixbuf

TRAYICON_UPDATE_INTERVAL = 5 # in seconds

class OneDrive_ObserverHandler(Gtk.StatusIcon):
	def __init__(self, log):
		GObject.GObject.__init__(self)
		self.display_name = 'gtk'
		self.logger = log
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
	
	def handle_start(self):
		GLib.timeout_add_seconds(TRAYICON_UPDATE_INTERVAL, self.update)
		Gtk.main()
	
	def handle_event(self, event_id, event_args):
		pass
	
	def handle_stop(self):
		pass
	