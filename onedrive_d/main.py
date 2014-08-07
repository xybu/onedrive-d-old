#!/usr/bin/python3

import sys
import config

thread_pool = []

def add_daemon_thread():
	import daemon
	thread_pool.append(daemon.OneDrive_DaemonThread())

def add_monitor_thread():
	import observer
	thread_pool.append(observer.OneDrive_ObserverThread())

def print_help():
	print('Usage: onedrive-d [--no-gui] [--help]')
	print('	--no-gui: start the daemon without GUI')
	print('	--help: print the usage information')
	print('Current version: ' + config.APP_VERSION + '')

def main():
	# print help info if '--help' is a cmd arg
	if '--help' in sys.argv:
		print_help()
		sys.exit(0)
	
	# start the daemon thread
	add_daemon_thread()
	
	if '--no-gui' not in sys.argv:
		# start the GUI thread unless the user prefers no
		add_monitor_thread()
	
	for t in thread_pool:
		t.start()
	
	for t in thread_pool:
		t.join()
	
if __name__ == "__main__":
	main()