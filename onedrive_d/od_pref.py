"""
Preference guide dispatcher for onedrive-d.
"""

import sys
import argparse


def main():
	pref_guide = None

	parser = argparse.ArgumentParser(prog='onedrive-pref',
		description='Configuration guide for onedrive-d program.',
		epilog='For technical support, visit http://github.com/xybu/onedrive-d/issues.')

	parser.add_argument('--ui', default='cli',
		choices=['cli', 'gtk'],
		help='specify the user interface. Default: cli')

	args = parser.parse_args()

	if args.ui == 'gtk':
		from . import od_pref_gtk
		pref_guide = od_pref_gtk.PreferenceGuide()
	else:
		from . import od_pref_cli
		pref_guide = od_pref_cli.PreferenceGuide()

	try:
		pref_guide.start()
	except (KeyboardInterrupt, EOFError):
		print('Exit.')
		sys.exit(0)

if __name__ == "__main__":
	main()
