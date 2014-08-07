#!/usr/bin/python3

import sys
import config

def start_daemon_thread():
	print "This function call should start a thread for the daemon."

def start_gui_thread():
	print "This function call should start a gui client thread."

def print_help():
	print 'Usage: onedrive-d [--no-gui] [--help]'
	print '	--no-gui: start the daemon without GUI'
	print '	--help: print the usage information'
	print 'Current version: ' + config.APP_VERSION

def main():
	# print help info if '--help' is a cmd arg
	if '--help' in sys.argv:
		print_help()
		sys.exit(0)
	
	# start the daemon thread
	start_daemon_thread()
	
	if '--no-gui' not in sys.argv:
		# start the GUI thread unless the user prefers no
		start_gui_thread()
	