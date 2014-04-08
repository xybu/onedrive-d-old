#!/usr/bin/python

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
	pass

# set-up packages?
class OneDrive_SetupWindow(gtk.Window):
	pass

# authorization panel
# local repository path
class OneDrive_SettingsWindow(gtk.Window):
	pass

# list the log
class OneDrive_MonitorWindow(gtk.Window):
	pass

# show the about info and possible updates
class OneDrive_AboutWindow(gtk.Window):
	pass

# issue a notification
class OneDrive_Notification:
	pass

if __name__ == "__main__":
	pass
