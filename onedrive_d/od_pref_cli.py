#!/usr/bin/python3

"""
Preference Guide (CLI version) for onedrive-d
"""

import sys
import os
import subprocess
from . import od_glob
config = od_glob.get_config_instance(setup_mode=True)
from . import od_onedrive_api

def query_yes_no(question, default='yes'):
	valid = {'yes': True, 'y': True, 'ye': True, 'no': False, 'n': False}
	if default is None:
		prompt = ' [y/n] '
	elif default == "yes":
		prompt = ' [Y/n] '
	elif default == "no":
		prompt = ' [y/N] '
	else:
		raise ValueError("invalid default answer: '%s'" % default)
	while True:
		choice = input(question + prompt).lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def mkdir_if_missing(path, uid):
	if not os.path.exists(path):
		print('The path "' + path + '" does not exist. Try creating it.')
		od_glob.mkdir(path, uid)
	if not os.path.isdir(path):
		print('Error: "' + path + '" is not a directory.')
		return False
	return True


class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


class PreferenceGuide:

	def __init__(self):
		self.api = od_onedrive_api.get_instance()

	def start(self):
		print(bcolors.HEADER + 'Setting up onedrive-d...' + bcolors.ENDC)
		self.authorize_app()
		print('')
		self.set_root_path()
		print('')
		self.set_config_params()
		print('')
		self.modify_ignore_list()
		print('')
		print(bcolors.HEADER + 'All steps are finished.' + bcolors.ENDC)

	def authorize_app(self):
		if not query_yes_no(bcolors.BOLD + '(STEP 1/4) Do you want to authorize sign in with your OneDrive account?' + bcolors.ENDC):
			print(bcolors.OKBLUE + 'Skipped.' + bcolors.ENDC)
			return
		print('\nYou will need to visit the OneDrive sign-in page in a browser, ')
		print('log in and authorize onedrive-d, and then copy and paste the ')
		print('callback URL, which should start with \n"%s".\n' % self.api.client_redirect_uri)
		print('\033[1mThe callback URL is the URL where the sign-in page finally goes blank.\033[21m\n')
		print('Please visit the sign-in URL in your browser:\n')
		print(self.api.get_auth_uri())
		callback_uri = input('\nPlease paste the callback URL:\n')
		try:
			tokens = self.api.get_access_token(uri=callback_uri)
			config.set_access_token(tokens)
			config.dump()
			print(
				bcolors.OKGREEN + 'onedrive-d has been successfully authorized.' + bcolors.ENDC)
		except od_onedrive_api.OneDriveAPIException as e:
			print(bcolors.WARNING + 'Error: failed to authorize the client with the given URL.' + bcolors.ENDC)
			print('%s' % e)

	def set_root_path(self):
		if not query_yes_no(bcolors.BOLD + '(STEP 2/4) Do you want to specify path to local OneDrive repository?' + bcolors.ENDC):
			print(bcolors.OKBLUE + 'Skipped.' + bcolors.ENDC)
			return
		path = input('Please enter the abs path to sync with your OneDrive (default: ' + config.OS_HOME_PATH + '/OneDrive): ').strip()
		if path == '':
			path = config.OS_HOME_PATH + '/OneDrive'
		result = False
		try:
			result = mkdir_if_missing(path, config.OS_USER_ID)
			if not result:
				raise ValueError('"{}" is not a path to directory.', path)
			config.params['ONEDRIVE_ROOT_PATH'] = path
			config.dump()
			print(bcolors.OKGREEN + 'Path successfully set.' + bcolors.ENDC)
		except Exception as e:
			print(bcolors.WARNING + 'Error: {}.'.format(e) + bcolors.ENDC)

	def set_config_params(self):
		if not query_yes_no(bcolors.BOLD + '(STEP 3/4) Do you want to change the numeric settings?' + bcolors.ENDC):
			print(bcolors.OKBLUE + 'Skipped.' + bcolors.ENDC)
			return
		inp = input('How many seconds to wait for before retrying a network failure (current: ' + str(config.params['NETWORK_ERROR_RETRY_INTERVAL']) + ')?').strip()
		if inp == '':
			inp = config.params['NETWORK_ERROR_RETRY_INTERVAL']
		else:
			try:
				inp = int(inp)
				config.params['NETWORK_ERROR_RETRY_INTERVAL'] = inp
			except Exception as e:
				print(bcolors.WARNING + 'Error: {}.'.format(e) + bcolors.ENDC)
				print(bcolors.WARNING + 'Value did not set.' + bcolors.ENDC)
		inp = input('\nFiles larger than what size (in MiB) will be uploaded blocks by blocks? (current: ' + str(config.params['BITS_FILE_MIN_SIZE'] / 2 ** 20) + ')?').strip()
		if inp == '':
			inp = config.params['BITS_FILE_MIN_SIZE']
		else:
			try:
				inp = int(inp)
				config.params['BITS_FILE_MIN_SIZE'] = inp * 2 ** 20
			except Exception as e:
				print(bcolors.WARNING + 'Error: {}.'.format(e) + bcolors.ENDC)
				print(bcolors.WARNING + 'Value did not set.' + bcolors.ENDC)
		inp = input('\nWhen a file is uploaded blocks by blocks, what is the block size (in KiB)? (current: ' + str(config.params['BITS_BLOCK_SIZE'] / 2 ** 10) + ')?').strip()
		if inp == '':
			inp = config.params['BITS_BLOCK_SIZE']
		else:
			try:
				inp = int(inp)
				config.params['BITS_BLOCK_SIZE'] = inp * 2 ** 10
			except Exception as e:
				print(bcolors.WARNING + 'Error: {}.'.format(e) + bcolors.ENDC)
				print(bcolors.WARNING + 'Value did not set.' + bcolors.ENDC)
		config.dump()

	def modify_ignore_list(self):
		if not query_yes_no(bcolors.BOLD + '(STEP 4/4) Do you want to edit the ignore list file?' + bcolors.ENDC):
			print(bcolors.OKBLUE + 'Skipped. You can manually edit "' + config.APP_IGNORE_FILE + '" at your convenience.' + bcolors.ENDC)
			return
		print('Calling your default editor...')
		subprocess.call(
			['${EDITOR:-vi} "' + config.APP_IGNORE_FILE + '"'], shell=True)
		print(
			bcolors.OKGREEN + 'You have exited from the text editor.' + bcolors.ENDC)
