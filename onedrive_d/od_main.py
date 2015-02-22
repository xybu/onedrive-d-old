#!/usr/bin/python3

'''
Main entry of onedrive-d.

Usage:
'''

import sys
from . import od_glob

def print_usage():
	print('Usage: ' + sys.argv[0] + ' [--ui=cli|gtk] [--help]')
	print('''Arguments:
	--ui: specify the user interface.
	      "cli" for command-line interface (default)
	      "gtk" for GTK-based GUI interface.
	--help: print usage information.
	''')

def main():
	daemon = None
	
	# parse command-line arguments
	for arg in sys.argv:
		if arg.lower() == '--help':
			print_usage()
			sys.exit(0)
		elif arg.startswith('--ui='):
			val = arg.split('=', maxsplit = 1)[1].lower()
			if val == 'gtk' and daemon == None:
				# use gtk version as long as gtk arg is given
				from . import od_daemon_gtk
				daemon = od_daemon_gtk.Daemon()
			elif val != 'cli':
				print('Error: unknown parameter "' + arg + '"')
				sys.exit(1)
	
	if daemon == None:
		from . import od_daemon_cli
		daemon = od_daemon_cli.Daemon()
	
	# start UI engine
	daemon.start()
	
if __name__ == "__main__":
	main()
