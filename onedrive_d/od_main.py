#!/usr/bin/python3

"""
Main entry of onedrive-d.
"""

import sys
import logging
import argparse
from . import od_glob


def main():
	daemon = None
	log_level = None

	parser = argparse.ArgumentParser(prog='onedrive-d',
		description='onedrive-d daemon program.',
		epilog='For technical support, visit http://github.com/xybu/onedrive-d/issues.')

	parser.add_argument('--log', default='DEBUG',
		choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
		help='specify the minimum log level. Default: DEBUG')

	parser.add_argument('--ui', default='cli',
		choices=['cli', 'gtk'],
		help='specify the user interface. Default: cli')

	args = parser.parse_args()

	if args.log[0] == 'D':
		log_level = logging.DEBUG
	elif args.log[0] == 'I':
		log_level = logging.INFO
	elif args.log[0] == 'W':
		log_level = logging.WARNING
	elif args.log[0] == 'E':
		log_level = logging.ERROR
	else:
		log_level = logging.CRITICAL
	logger = od_glob.get_logger(log_level)

	if args.ui == 'cli':
		from . import od_daemon_cli
		daemon = od_daemon_cli.Daemon()
	else:
		from . import od_daemon_gtk
		daemon = od_daemon_gtk.Daemon()

	# start UI engine
	daemon.start()

if __name__ == "__main__":
	main()
