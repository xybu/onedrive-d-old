#!/usr/bin/python3

import os
import sys
import json
import config
import threading
import logger

class OneDrive_DaemonThread(threading.Thread):
	
	def __init__(self):
		super().__init__()
		self.name = 'daemon'
		self.daemon = True
		# the daemon prints to stderr
		self.logger = logger.Logger(None, config.LOGGING_MIN_LEVEL)
		self.observer_list = []
		
	def run(self):
		self.logger.debug('started running.')
	
	def add_observer(self, observer_id):
		self.observer_list.append(observer_id)
		self.logger.debug('added an observer called ' + observer_id.name)
	
	
	