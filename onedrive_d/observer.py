#!/usr/bin/python3

import os
import threading
import subprocess
import config
import logger

'''
An observer handler OneDrive_ObserverHandler should implement 
the following functions:
	__init__(self, log)
	self.display_name
	handle_event(self, event_id, event_args)
	handle_start(self)
	handle_stop(self)
'''

class OneDrive_ObserverThread(threading.Thread):
	
	def __init__(self, handler_name = 'gtk'):
		super().__init__()
		self.name = 'observer'
		self.daemon = True
		self.logger = logger.Logger(config.LOGGING_FILE_PATH, config.LOGGING_MIN_LEVEL)
		
		if handler_name == 'gtk':
			from handler_icon import OneDrive_ObserverHandler
		else:
			from handler_cmd import OneDrive_ObserverHandler
		
		self.handler = OneDrive_ObserverHandler(log = self.logger)
	
	def handle_event(self, event_id, event_args):
		self.handler.handle_event(event_id, event_args)
	
	def run(self):
		self.logger.debug('start running')
		if self.handler == None:
			self.logger.critical('No observer handler is registered.')
			sys.exit(1)
		self.logger.debug('use handler called ' + self.handler.display_name)
		self.handler.handle_start()
	