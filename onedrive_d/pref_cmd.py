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
		if not query_yes_no('\nDo you want to authorize onedrive-d to access your OneDrive account?'):
			print('Skipped.')
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
		if not query_yes_no('\nDo you want to specify the path to local OneDrive repository?'):
			print('Skipped')
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
	
	def show_ignore_list_dialog(self):
		if not query_yes_no('\nDo you want to edit the ignore list?'):
			print('Skipped')
			return
		config.load_ignore_list()
		print('Calling your default editor...')
		subprocess.call(['${EDITOR:-vi} "' + config.APP_CONFIG_PATH + '/ignore_list.txt"'], shell = True)
		print('You have exited from the text editor.')
	
	def start(self):
		config.load_config()
		self.show_auth_dialog()
		self.show_basedir_dialog()
		self.show_ignore_list_dialog()
		print('\nAll steps have been gone through.')
