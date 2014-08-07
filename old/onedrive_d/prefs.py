#!/usr/bin/python

import os
import sys
import pwd
import gtk, gobject
import json
import config
from onedrive import api_v5

def mkdirIfMissing(path):
	try:
		if not os.path.exists(path):
			os.mkdir(path, 0700)
			os.chown(path, pwd.getpwnam(config.LOCAL_USER).pw_uid, pwd.getpwnam(config.LOCAL_USER).pw_gid)
		return True
	except OSError as e:
		print "OSError({0}): {1}".format(e.errno, e.strerror)
		return False

class OneDrive_AuthWindow(gtk.Window):
	webView = None
	liveAPI = None
	parentWindow = None
	
	def __init__(self, api = None, parentWindow = None):
		import webkit
		super(OneDrive_AuthWindow, self).__init__()
		self.webView = webkit.WebView()
		self.webView.connect("load-finished", self.page_loaded)
		self.add(self.webView)
		self.set_default_size(360, 500)
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_title("Connect to OneDrive.com")
		self.connect('delete-event', self.close_window)
		self.connect('destroy', self.close_window)
		
		if api != None:
			self.liveAPI = api
		
		if parentWindow != None:
			self.parentWindow = parentWindow
		
		self.webView.open(api.auth_user_get_url() + "&display=touch")
		
		self.show_all()
	
	def page_loaded(self, webview, frame, data = None):
		url = frame.get_uri()
		if "https://login.live.com/oauth20_desktop.srf" in url:
			try:
				self.liveAPI.auth_user_process_url(url)
				self.liveAPI.auth_get_token()
				os.chown(config.HOME_PATH + "/.lcrc", pwd.getpwnam(config.LOCAL_USER).pw_uid, pwd.getpwnam(config.LOCAL_USER).pw_gid)
				
				if self.parentWindow != None:
					self.parentWindow.refresh()
				
				self.hide_all()
				self.close_window(self, webview)
			except api_v5.AuthenticationError as e:
				print "Authentication failed."
	
	def close_window(self, widget, args = None):
		if self.parentWindow != None:
			self.parentWindow.authWindow = None
		del self
	
class OneDrive_SettingsWindow(gtk.Window):
	timer = None
	liveAPI = None
	authWindow = None
	authTextLabel = None
	locationChooser = None
	
	def __init__(self, api = None):
		super(OneDrive_SettingsWindow, self).__init__()
		self.set_title("Settings | OneDrive-D")
		self.set_border_width(5)
		# self.set_size_request(400, 500)
		self.set_position(gtk.WIN_POS_CENTER)
		
		vbox = gtk.VBox(False, 5)
		hbox = gtk.HBox(True, 3)
		
		valign = gtk.Alignment(1, 1, 1, 1)
		valign.set_padding(10, 10, 10, 10)
		vbox.pack_start(valign)
		
		saveButton = gtk.Button(stock = gtk.STOCK_OK)
		saveButton.set_size_request(75, 35)
		saveButton.connect("clicked", self.save_settings)
		closeButton = gtk.Button(stock = gtk.STOCK_CLOSE)
		closeButton.connect("clicked", self.exit_window)
		hbox.add(saveButton)
		hbox.add(closeButton)
		halign = gtk.Alignment(1, 0, 0, 0)
		halign.add(hbox)
		
		contentTable = gtk.Table(rows = 4, columns = 2, homogeneous = False)
		
		authLabel = gtk.Label(str = "Authentication")	
		authTable = gtk.Table(rows = 2, columns = 1)
		authButton = gtk.Button(label = "Connect to OneDrive.com")
		authButton.connect("clicked", self.open_auth_window)
		self.authTextLabel = gtk.Label("Check authentication status...")
		authTable.attach(self.authTextLabel, 0, 1, 0 ,1, ypadding = 1)
		authTable.attach(authButton, 0, 1, 1, 2, ypadding = 1)
		
		locationLabel = gtk.Label(str = "Location")
		locationTable = gtk.Table(rows = 2, columns = 1)
		location_helpText = gtk.Label("The local folder to sync with your OneDrive.")
		self.locationChooser = gtk.FileChooserButton(self.create_filechooser_dialog())
		self.locationChooser.connect("file-set", self.location_chosen)
		locationTable.attach(location_helpText, 0, 1, 0, 1, xpadding = 1)
		locationTable.attach(self.locationChooser, 0, 1, 1, 2, xpadding = 1)
		
		exclusionLabel = gtk.Label(str = "Exclusions")
		exclusionTable = gtk.Table(rows = 7, columns = 1)
		exclude_helpText = gtk.Label(str = "Exclude the following types of files when syncing:")
		self.exclude_WinFiles = gtk.CheckButton(label = "Microsoft Windows-only files (e.g., \"Desktop.ini\")")
		self.exclude_MacFiles = gtk.CheckButton(label = "Apple Mac OS-only files (e.g., \".DS__Store\")")
		self.exclude_LinuxTempFiles = gtk.CheckButton(label = "Typical Linux temporary files (e.g., \"hello.c~\")")
		self.exclude_VimTempFiles = gtk.CheckButton(label = "Vi temporary files (e.g., \"hello.c.swp\")")
		self.exclude_EmacsTempFiles = gtk.CheckButton(label = "Emacs temporary files (e.g., \"#hello.c#\")")
		
		exclude_Note = gtk.Label(str = """note: files whose names are not supported 
by NTFS namespace (e.g., "hello.c?") are 
excluded automatically.""")
		
		# Load saved settings
		if config.CONF != None:
			try:
				self.exclude_WinFiles.set_active(config.CONF["exclude_WinFiles"])
				self.exclude_MacFiles.set_active(config.CONF["exclude_MacFiles"])
				self.exclude_LinuxTempFiles.set_active(config.CONF["exclude_LinuxTempFiles"])
				self.exclude_VimTempFiles.set_active(config.CONF["exclude_VimTempFiles"])
				self.exclude_EmacsTempFiles.set_active(config.CONF["exclude_EmacsTempFiles"])
				self.locationChooser.set_filename(config.CONF["rootPath"])
			except:
				pass
		else:
			self.exclude_WinFiles.set_active(True)
			self.exclude_MacFiles.set_active(True)
			self.exclude_LinuxTempFiles.set_active(True)
			self.exclude_VimTempFiles.set_active(True)
			self.exclude_EmacsTempFiles.set_active(True)
		
		exclusionTable.attach(exclude_helpText, 0, 1, 0, 1, ypadding = 3)
		exclusionTable.attach(self.exclude_WinFiles, 0, 1, 1, 2, ypadding = 1)
		exclusionTable.attach(self.exclude_MacFiles, 0, 1, 2, 3, ypadding = 1)
		exclusionTable.attach(self.exclude_LinuxTempFiles, 0, 1, 3, 4, ypadding = 1)
		exclusionTable.attach(self.exclude_VimTempFiles, 0, 1, 4, 5, ypadding = 1)
		exclusionTable.attach(self.exclude_EmacsTempFiles, 0, 1, 5, 6, ypadding = 1)
		exclusionTable.attach(exclude_Note, 0, 1, 6, 7, ypadding = 1)
		
		contentTable.attach(authLabel, 0, 1, 0, 1, xpadding = 5, ypadding = 10)
		contentTable.attach(authTable, 1, 2, 0, 1, xpadding = 5, ypadding = 10)
		contentTable.attach(locationLabel, 0, 1, 1, 2, xpadding = 5, ypadding = 10)
		contentTable.attach(locationTable, 1, 2, 1, 2, xpadding = 5, ypadding = 10)
		contentTable.attach(exclusionLabel, 0, 1, 2, 3, xpadding = 5, ypadding = 10)
		contentTable.attach(exclusionTable, 1, 2, 2, 3, xpadding = 5, ypadding = 10)
		
		valign.add(contentTable)
		
		vbox.pack_start(halign, False, False, 3)
		
		self.add(vbox)
		
		self.connect("delete-event", self.exit_window)
		self.connect("destroy", gtk.main_quit)
		
		self.timer = gobject.timeout_add(200, self.start_task)
		
		if api != None:
			self.liveAPI = api
		
		self.show_all()
	
	def create_filechooser_dialog(self):
		d = gtk.FileChooserDialog(title = "Choose your local OneDrive folder", parent = self, action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		d.set_default_response(gtk.RESPONSE_OK)
		return d
	
	def start_task(self):
		gobject.source_remove(self.timer)
		self.refresh()
	
	def refresh(self):
		try:
			self.liveAPI.get_quota()
			self.authTextLabel.set_text("You have connected to OneDrive.com.")
		except:
			self.authTextLabel.set_text("You have not authenticated OneDrive-d yet.")
	
	def open_auth_window(self, widget, args = None):
		if self.authWindow == None:
			self.authWindow = OneDrive_AuthWindow(api = self.liveAPI, parentWindow = self)
	
	def location_chosen(self, widget, args = None):
		# do some sanity check if needed
		pass
	
	def serialize_settings(self):
		configuration = {
			"rootPath": self.locationChooser.get_filename(),
			"exclude": [".*[<>?\*:\"\|]+.*"],
			"exclude_WinFiles": self.exclude_WinFiles.get_active(),
			"exclude_MacFiles": self.exclude_MacFiles.get_active(),
			"exclude_LinuxTempFiles": self.exclude_LinuxTempFiles.get_active(),
			"exclude_VimTempFiles": self.exclude_VimTempFiles.get_active(),
			"exclude_EmacsTempFiles": self.exclude_EmacsTempFiles.get_active()
		}
	
		if self.exclude_WinFiles.get_active():
			configuration["exclude"] += "~\$.*\.*|.*\.laccdb|Desktop\.ini|Thumbs\.db|EhThumbs\.db".split("|")
		
		if self.exclude_LinuxTempFiles.get_active():
			configuration["exclude"] += ".*~|\.lock".split("|")
		
		if self.exclude_VimTempFiles.get_active():
			configuration["exclude"] += ".netrwhist|\.directory|Session\.vim|[._]*.s[a-w][a-z]|[._]s[a-w][a-z]|.*\.un~".split("|")
		
		if self.exclude_EmacsTempFiles.get_active():
			configuration["exclude"] += "\#.*\#|\.emacs\.desktop|\.emacs\.desktop\.lock|.*\.elc|/auto-save-list|\.\#.*|\.org-id-locations|.*_flymake\..*".split("|")
		
		if self.exclude_MacFiles.get_active():
			configuration["exclude"] += "\.DS_Store|Icon.|\.AppleDouble|\.LSOverride|\._.*|\.Spotlight-V100|\.Trashes".split("|")
		
		configuration["exclude"] = "^(" + "|".join(configuration["exclude"]) + ")$"
		return configuration
	
	def save_settings(self, widget, args = None):
		if self.locationChooser.get_filename() == None:
			d = gtk.MessageDialog(parent = self, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, message_format = "You did not choose a local folder to save your OneDrive files. Please check.")
			response = d.run()
			if response == gtk.RESPONSE_OK:
				d.destroy()
			return False
		
		configuration = self.serialize_settings()
	
		CONF_PATH = config.HOME_PATH + "/.onedrive/user.conf"
		f = open(CONF_PATH, "w")
		f.write(json.dumps(configuration))
		f.close()
		os.chown(CONF_PATH, pwd.getpwnam(config.LOCAL_USER).pw_uid, pwd.getpwnam(config.LOCAL_USER).pw_gid)
		os.chmod(CONF_PATH, 0600)
		
		info = gtk.MessageDialog(parent = self, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, message_format = "Your preferences have been saved successfully.")
		response = info.run()
		if response == gtk.RESPONSE_OK:
			info.destroy()
			del info
			del response
		
	def exit_window(self, widget, args = None):
		try:
			CONF_PATH = config.HOME_PATH + "/.onedrive/user.conf"
			f = open(CONF_PATH, "r")
			old_settings = f.read()
			f.close()
			del f
		except:
			old_settings = ""
		
		if old_settings != json.dumps(self.serialize_settings()):
			c = gtk.MessageDialog(parent = self, type = gtk.MESSAGE_QUESTION, buttons = gtk.BUTTONS_YES_NO, message_format = "Your settings has been modified. Do you want to save your settings before exitting?")
			response = c.run()
			if response == gtk.RESPONSE_YES:
				if not self.save_settings(widget):
					c.destroy()
					return True
			else:
				c.destroy()
		
		gtk.main_quit()
		return False
	
def main():
	
	assert mkdirIfMissing(config.HOME_PATH + "/.onedrive"), "Failed to create the configuration directory \"" + config.HOME_PATH + "/.onedrive" + "\"."
	
	if not os.path.exists(config.HOME_PATH + "/.lcrc"):
		f = open(config.HOME_PATH + "/.lcrc", "w")
		f.write("client:\n  id: " + config.APP_CREDS[0] + "\n  secret: " + config.APP_CREDS[1] + "\n")
		f.close()
		os.chown(config.HOME_PATH + "/.lcrc", pwd.getpwnam(config.LOCAL_USER).pw_uid, pwd.getpwnam(config.LOCAL_USER).pw_gid)
		os.chmod(config.HOME_PATH + "/.lcrc", 0600)
	
	API = api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
	
	gtk.gdk.threads_init()
	gobject.threads_init()
	OneDrive_SettingsWindow(api = API)
	gtk.main()

if __name__ == "__main__":
	main()

