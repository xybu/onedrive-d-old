#!/usr/bin/python3

import sys
import config
import live_api
import logger

from daemon import OneDrive_DaemonThread
from observer import OneDrive_ObserverThread

'''
The daemon should implement the following functions:
	add_observer(self, observer_id)

An observer should implement the following functions:
	handle_event(self, event_id, event_args)
	self.name
'''

def print_help():
	print('Usage: onedrive-d [--no-gui] [--help] [--no-prompt]')
	print('	--no-gui: start the program without GUI components')
	print('	--help: print the usage information')
	print('	--no-prompt: when errors like auth failure occur, terminate program rather than showing dialogs')
	print('Current version: ' + config.APP_VERSION + '')

def main():
	# print help info if '--help' is a cmd arg
	if '--help' in sys.argv:
		print_help()
		sys.exit(0)
	
	handler_name = 'gtk'
	if '--no-gui' in sys.argv:
		handler_name = 'default'
	
	try:
		config.load_config()
	except:
		print('The configuration file either corrupted or does not exist. Rebuild.')
		config.reset_config()
		config.load_config()
	
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
	
	observer_thread = OneDrive_ObserverThread(handler_name = handler_name)
	
	daemon_thread = OneDrive_DaemonThread()
	daemon_thread.add_observer(observer_thread)
	
	daemon_thread.start()
	observer_thread.start()
	
	daemon_thread.join()
	observer_thread.join()
	
if __name__ == "__main__":
	main()