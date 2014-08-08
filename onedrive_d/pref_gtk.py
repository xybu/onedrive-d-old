#!/usr/bin/python3

import urllib
import config
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import WebKit

GLib.threads_init()

class OneDrive_PreferenceDialog(Gtk.Window):
	
	def __init__(self, api):
		super().__init__()
		self.api = api
		self.connect('destroy', Gtk.main_quit)
		self.show_all()
	
	def handle(self, event_id, event_args = None):
		print('Dialog object received {} event.'.format(event_id))
		if event_id == 'refresh_code':
			app_tokens = self.api.get_access_token(uri = event_args)
			config.save_token(app_tokens)
			config.save_config()
		elif event_id == 'child_close':
			pass
	
	def show_auth_dialog(self):
		OneDrive_WebkitAuthWindow(api = self.api, parent = self).run()
	
	def show_basedir_dialog(self):
		pass
	
	def start(self):
		Gtk.main()
		self.show_basedir_dialog()
		self.show_auth_dialog()
		# TODO: trigger the quit by some other mechanism

class OneDrive_WebkitAuthWindow(Gtk.Window):
	def __init__(self, api, parent = None):
		super().__init__()
		self.api = api
		self.parent = parent
		self.web_view = WebKit.WebView()
		self.web_view.connect('load-finished', self.on_page_loaded)
		self.add(self.web_view)
		self.set_title("Connect to OneDrive.com")
		self.set_default_size(360, 480)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.connect('delete-event', self.on_window_close)
		self.connect('destroy', Gtk.main_quit)
		self.show_all()
	
	def on_page_loaded(self, view, frame, args = None):
		page_uri = frame.get_uri()
		if page_uri.startswith(self.api.client_redirect_uri):
			if self.parent != None:
				self.parent.handle('refresh_code', page_uri)
			self.on_window_close(view, None)
		
	def on_window_close(self, widget, args = None):
		self.hide()
		del self.web_view
		if self.parent == None:
			Gtk.main_quit()
		if self.parent != None:
			self.parent.handle('child_close')
			del self
	
	def run(self):
		GLib.idle_add(self.web_view.load_uri, self.api.get_auth_uri())
		if self.parent == None:
			Gtk.main()