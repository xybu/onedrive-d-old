#!/usr/bin/python3

import os
import sys
import json
import config
import threading
import logger

class OneDrive_DaemonThread(threading.Thread):
	
	def __init__(self, log_path = None, log_min_level = logger.Logger.NOTSET):
		super().__init__()
		self.name = 'daemon'
		self.daemon = True
		self.logger = logger.Logger(log_path, log_min_level)
		
	def run(self):
		self.logger.debug("This function call should start a thread for the daemon.")
	