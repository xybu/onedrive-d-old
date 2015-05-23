"""
Pereference wizard program using command-line interface.
It guides user to set up the configurations step by step.
"""

import os
import sys
import shutil

from . import od_bootstrap
from . import od_account


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


class bcolors:
	BLUE = '\033[96m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	RED = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


class PreferenceGuide:
	def __init__(self):
		self.user_info = od_account.get_user_info()
		self.config_info = od_account.get_user_config(self.user_info)
		self.logger = od_bootstrap.get_logger()
		if self.config_info is None:
			if not os.path.isdir(od_account.ACCOUNT_INVENTORY):
				try:
					shutil.rmtree(od_account.ACCOUNT_INVENTORY)
				except:
					pass
				try:
					# create dir owned by root
					od_bootstrap.mkdir(od_account.ACCOUNT_INVENTORY, 0, 0)
				except OSError as e:
					self.logger.critical('Failed to create directory "{0}" as root - {1} (005.{2}).'.format(od_account.ACCOUNT_INVENTORY, e.strerror, e.errno))
					sys.exit(1)
			# TODO: format config information
		else:
			pass

	def start(self):
		while True:
			print(bcolors.BLUE + bcolors.BOLD + 'Select one action from the following list:' + bcolors.ENDC)
			print(bcolors.BLUE + '1. Add a new OneDrive account' + bcolors.ENDC)
			print(bcolors.BLUE + '2. Edit a linked OneDrive account' + bcolors.ENDC)
			print(bcolors.BLUE + '3. Remove a linked OneDrive account' + bcolors.ENDC)
			print(bcolors.BLUE + '4. Change onedrive-d settings' + bcolors.ENDC)
			print(bcolors.BLUE + '5. Exit wizard' + bcolors.ENDC)
			choice = input(bcolors.BOLD + 'Which action do you want to perform (1-5): ' + bcolors.ENDC).strip()
			if choice == '1':
				add_onedrive_account()
			elif choice == '2':
				edit_onedrive_account()
			elif choice == '3':
				remove_onedrive_account()
			elif choice == '4':
				change_settings()
			elif choice == '5':
				sys.exit(0)
			else:
				print(bcolors.RED + 'Error: unrecognized action number "' + choice + '".' + bcolors.ENDC)

	def add_onedrive_account(self):
		pass

	def list_onedrive_account(self):
		pass

	def edit_onedrive_account(self):
		pass

	def remove_onedrive_account(self):
		pass

	def change_settings(self):
		pass
