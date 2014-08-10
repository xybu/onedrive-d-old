#!/usr/bin/python3

'''
The entry point for `onedrive-pref` command.
'''

import sys
import config
import live_api

def print_help():
	print('onedrive-pref [--no-gui] [--log-out] [--help]')
	print('	--no-gui: interact through the command-line interface, ')
	print('	          instead of using a window')
	print('	--log-out: remove the stored tokens to log the user out.')
	print('	--help: show help information.')
	print('')
	print('Current version: ' + config.APP_VERSION + '')

def main():
	
	if '--help' in sys.argv:
		print_help()
		sys.exit(0)
	
	if '--log-out' in sys.argv:
		config.unset_config('token')
		config.unset_config('token_expiration')
		config.save_config()
		print('The log-in tokens have been successfully deleted.')
		sys.exit(0)
	
	if '--no-gui' in sys.argv:
		from pref_cmd import OneDrive_PreferenceDialog
	else:
		from pref_gtk import OneDrive_PreferenceDialog
	
	api = live_api.OneDrive_API(config.APP_CLIENT_ID, config.APP_CLIENT_SECRET)
	
	OneDrive_PreferenceDialog(api = api).start()
	
if __name__ == "__main__":
	main()
