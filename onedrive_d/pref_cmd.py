#!/usr/bin/python3

import os

class OneDrive_PreferenceDialog:
	
	def __init__(self, api):
		self.api = api
	
	def show_auth_dialog(self):
		pass
	
	def show_basedir_dialog(self):
		pass
	
	def start(self):
		self.show_basedir_dialog()
		self.show_auth_dialog()
