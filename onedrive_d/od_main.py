#!/usr/bin/python3

"""
Main entry of onedrive-d.
"""

import sys
import click
import daemonocle
from . import od_glob

# this runs before any daemonocle code
config = od_glob.get_config_instance()
is_debug_mode = False
for arg in sys.argv:
	if arg == '--debug':
		od_glob.get_logger(config.params['MIN_LOG_LEVEL']).debug('running in debug mode.')
		is_debug_mode = True
		break
if not is_debug_mode:
	od_glob.get_logger(config.params['MIN_LOG_LEVEL'], config.params['LOG_FILE_PATH']).debug('running in daemon node.')


@click.command(cls=daemonocle.cli.DaemonCLI, daemon_params={'pidfile': config.APP_CONF_PATH + '/onedrive.pid'})
def main():
	mon = None
	if not config.params['USE_GUI']:
		from . import od_mon_cli
		mon = od_mon_cli.Monitor()
	else:
		from . import od_mon_gtk
		mon = od_mon_gtk.Monitor()

	# start monitor engine
	try:
		mon.start()
	except KeyboardInterrupt:
		# for debugging, dump task db
		mon.stop()

if __name__ == "__main__":
	main()
