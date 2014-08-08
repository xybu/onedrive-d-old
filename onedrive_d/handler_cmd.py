#!/usr/bin/python3

import sys
import config

'''
The default handler that simply records the events in the logger.

handler_name: default
'''

class OneDrive_ObserverHandler:
	
	def __init__(self, log):
		self.display_name = 'cmd handler'
		self.logger = log
	
	def handle_event(self, event_id, event_args):
		pass
	
	def handle_start(self):
		pass
	
	def handle_stop(self):
		pass
	
