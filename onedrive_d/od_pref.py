#!/usr/bin/python3

'''
Preference guide dispatcher for onedrive-d.

Usage: ./od_pref.py [--ui=cli|gtk]
params:
	--ui: specify the user interface. "cli" for command-line interface and "gtk" for GUI.
	      If not given, use default value "cli".
	
Notes:
 * GUI is not implemented yet.
'''

import sys

def print_usage():
	print('Usage: ' + sys.argv[0] + ' [--ui=cli|gtk] [--help]')
	print('''Arguments:
	--ui: specify the user interface. 
	      "cli" for command-line interface (default when not given)
	      "gtk" for GUI interface.
	--help: print usage information.
''')

def main():
	pref_guide = None
	
	for arg in sys.argv:
		if arg.startswith('--ui='):
			val = arg.split('=', maxsplit = 1)[1].lower()
			if val == 'gtk' and pref_guide == None:
				# use gtk version as long as gtk arg is given
				from od_pref_gtk import PreferenceGuide
				pref_guide = PreferenceGuide()
			elif val != 'cli':
				print('Error: unknown parameter "' + arg + '"')
				sys.exit(1)
		elif arg.lower() == '--help':
			print_usage()
			sys.exit(0)
	
	if pref_guide == None:
		from od_pref_cli import PreferenceGuide
		pref_guide = PreferenceGuide()
	
	pref_guide.start()

if __name__ == "__main__":
	main()
