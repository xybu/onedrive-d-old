#!/usr/bin/python

import os
import sys
import config
import gtk, webkit
from onedrive import api_v5

def OneDrive_loadAuthPage(webview, frame, data=None):
	url = frame.get_uri()
	if "https://login.live.com/oauth20_desktop.srf" in url:
		try:
			API.auth_user_process_url(url)
			API.auth_get_token()
			import pwd
			os.chown(config.HOME_PATH + "/.lcrc", pwd.getpwnam(config.LOCAL_USER).pw_uid, pwd.getpwnam(config.LOCAL_USER).pw_gid)
			win.hide_all()
			gtk.main_quit()
			print "Authentication succeeded."
		except:
			print "Authentication failed."
			sys.exit(1)

if __name__ == "__main__":
	if not os.path.exists(config.HOME_PATH + "/.lcrc"):
		f = open(config.HOME_PATH + "/.lcrc", "w")
		f.write("client:\n  id: " + config.APP_CREDS[0] + "\n  secret: " + config.APP_CREDS[1] + "\n")
		f.close()
	
	API = api_v5.PersistentOneDriveAPI.from_conf("~/.lcrc")
	
	liveView = webkit.WebView()
	liveView.connect("load-finished", OneDrive_loadAuthPage)
	win = gtk.Window(gtk.WINDOW_TOPLEVEL)
	win.set_default_size(360, 500)
	win.set_position(gtk.WIN_POS_CENTER)
	win.set_title("Authenticate OneDrive-d")
	win.connect('destroy', gtk.main_quit)
	win.connect('delete-event', gtk.main_quit)
	win.add(liveView)
	win.show_all()
	liveView.open(API.auth_user_get_url() + "&display=touch")
	gtk.main()

