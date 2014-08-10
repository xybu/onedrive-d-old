#!/usr/bin/python3

import sys
import os
import subprocess

import config
from live_api import OneDrive_Error

def query_yes_no(question, default='yes'):
	valid = {'yes': True, 'y': True, 'ye': True, 'no': False, 'n': False}
	if default is None: prompt = ' [y/n] '
	elif default == "yes": prompt = ' [Y/n] '
	elif default == "no": prompt = ' [y/N] '
	else: raise ValueError("invalid default answer: '%s'" % default)
	while True:
		choice = input(question + prompt).lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def mkdir_if_missing(path):
	if not os.path.exists(path):
		print('The path "' + path + '" does not exist. Try creating it.')
		config.mkdir(path)
	if not os.path.isdir(path):
		print('ERROR: "' + path + '" is not a directory.')
		return False
	return True

class OneDrive_PreferenceDialog:
	
	def __init__(self, api):
		self.api = api
	
	def show_auth_dialog(self):
		print('=' * 30)
		if not query_yes_no('Do you want to authorize onedrive-d to access your OneDrive account?'):
			print('	Skipped.')
			return
		print('\nYou will need to visit the OneDrive authorization page manually, ')
		print('log in and authorize the onedrive-d, and then copy and paste the ')
		print('callback URL, which should start with \n"%s".\n' % self.api.client_redirect_uri)
		print('The callback url is the URL when the authorization page finally goes blank.\n')
		print('Please visit the authorization page via URL:\n')
		print(self.api.get_auth_uri())
		callback_uri = input('\nPlease paste the callback URL:\n')
		try:
			app_tokens = self.api.get_access_token(uri = callback_uri)
			config.save_token(app_tokens)
			config.save_config()
			print('\nonedrive-d has been successfully authorized.')
		except OneDrive_Error as e:
			print('CRITICAL: failed to authorize the client with the given URL.')
			print('%s' % e)
	
	def show_basedir_dialog(self):
		print('=' * 30)
		if not query_yes_no('Do you want to specify the path to local OneDrive repository?'):
			print('	Skipped')
			return
		path = input('Please enter the abs dir path to sync with your OneDrive (default: ' + config.USER_HOME_PATH + '/OneDrive): ').strip()
		if path == '': path = config.USER_HOME_PATH + '/OneDrive'
		result = False
		try:
			result = mkdir_if_missing(path)
		except OSError as e:
			print('OSError {}.'.format(e))
		
		if not result:
			print('CRITICAL: the path cannot be used for syncing.')
		else:
			config.set_config('base_path', path)
			config.save_config()
			print('Now use "%s" as the OneDrive base path.' % path)
	
	def show_log_path_dialog(self):
		print('=' * 30)
		if 'log_path' not in config.APP_CONFIG: config.set_config('log_path', None)
		if config.APP_CONFIG['log_path'] == None: display_log_path = 'stderr'
		else: display_log_path = config.APP_CONFIG['log_path']
		print('Current file path to display logs: ' + display_log_path)
		if not query_yes_no('Do you want to change this to another path?'):
			print('	Skipped')
			return
		print('WARNING: the specified file will be overwritten!')
		path = input('new abs file path ([Enter] for stderr): ') .strip()
		if path == '': path = None
		else:
			try:
				with open(path, 'w') as f:
					f.write('')
			except:
				print('Error: "' + path + '" is not a writable file path.')
				return
		config.set_config('log_path', path)
		config.save_config()
		if path == None: path = 'stderr'
		print('Now use ' + path + ' to show logs.')
	
	def show_ignore_list_dialog(self):
		print('=' * 30)
		if not query_yes_no('Do you want to edit the ignore list?'):
			print('	Skipped')
			return
		config.load_ignore_list()
		print('	Format: One wildcard expression per line.')
		print('	        Lines that start with "//" or are empty will be ignored.')
		if query_yes_no('Hit [Enter] or [y] to edit file ignore list.', 'yes'):
			print('	Calling your default editor...')
			subprocess.call(['${EDITOR:-vi} "' + config.APP_CONFIG_PATH + '/ignore_list.txt"'], shell = True)
			print('	You have exited from the text editor.')
		else:
			print('	You may edit the file "' + config.APP_CONFIG_PATH + '/ignore_list.txt" manually.')
	
	def start(self):
		self.show_auth_dialog()
		self.show_basedir_dialog()
		self.show_log_path_dialog()
		self.show_ignore_list_dialog()
		config.save_config()
		print('\nAll steps have been gone through.')
