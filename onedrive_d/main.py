#!/usr/bin/python3

import sys
import time
import config
import threading
import live_api
import logger

DAEMON_PULL_INTERVAL = 90

'''
The daemon should implement the following functions:
	add_observer(self, observer_id)
	run(self)
	stop(self)

An observer should implement the following functions:
	__init__(self)
	name
	notify()
'''

def print_help():
	print('Usage: onedrive-d [--ui=gtk] [--help] [--no-prompt]')
	print('	--ui: specify the UI component. Support "gtk". ')
	print('	      If not given, start daemon without UI.')
	print('	--help: print the usage information')
	print('	--no-prompt: when errors like auth failure occur, terminate program rather than showing dialogs')
	print('Current version: ' + config.APP_VERSION + '')

def main():
	# print help info if '--help' is a cmd arg
	if '--help' in sys.argv:
		print_help()
		sys.exit(0)
	
	api = live_api.OneDrive_API(config.APP_CLIENT_ID, config.APP_CLIENT_SECRET)
	
	app_tokens = config.get_token()
	if app_tokens == None:
		token_invalid = True
		if config.has_token():
			# try to refresh the token
			try:
				app_tokens = api.refresh_token(config.APP_CONFIG['token']['refresh_token'])
				config.save_token(app_tokens)
				config.save_config()
				token_invalid = False
			except live_api.NetworkError:
				print('Failed to reach OneDrive server. Please check your internet connection.')
				sys.exit(1)
			except live_api.AuthError:
				print('The client authorization has expired.')
				if '--no-prompt' in sys.argv:
					print('Please run `onedrive-prefs` to authorize the client.')
					sys.exit(1)
		if token_invalid:
			# failed to renew the token, show pref dialog
			# the pref program should guide users to set up all confs.
			if '--no-gui' in sys.argv:
				pass
			else:
				pass
	
	if not config.test_base_path():
		print('Path of local OneDrive repository is unset or invalid. Exit.')
		sys.exit(1)
	
	api.set_access_token(config.APP_CONFIG['token']['access_token'])
	
	# now start the threads
	# the MainThread is used for heart-beating
	
	from daemon import OneDrive_DaemonThread
	daemon_lock = threading.Event()
	daemon_thread = OneDrive_DaemonThread(api, daemon_lock)
	
	ui_component = ''
	for arg in sys.argv:
		if arg.startswith('--ui='):
			ui_component = arg.split('=')[1]
			break
	
	observer_thread = None
	if ui_component == 'gtk':
		from observer_gtk import OneDrive_Observer
		observer_thread = OneDrive_Observer()
	elif ui_component == 'dummy':
		from observer_dummy import OneDrive_Observer
		observer_thread = OneDrive_Observer()
	elif ui_component != '':
		print('The UI component "' + ui_component + '" is not found. Exit.')
		sys.exit(1)
	
	if observer_thread != None:
		daemon_thread.add_observer(observer_thread)
		observer_thread.start()
	
	# heart-beating for MainThread
	try:
		daemon_thread.start()
		while True:
			daemon_lock.set()
			time.sleep(DAEMON_PULL_INTERVAL)
	except KeyboardInterrupt:
		config.log.info('propagating stop signals.')
		daemon_thread.stop()
		if observer_thread != None:
			observer_thread.stop()
			observer_thread.join()
		daemon_thread.join()
		sys.exit(0)
	
if __name__ == "__main__":
	main()
