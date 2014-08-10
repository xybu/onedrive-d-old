#!python3

from time import sleep
import threading
import config

DAEMON_PULL_INTERVAL = 20		

class OneDrive_Observer(threading.Thread):
	def __init__(self, daemon_lock):
		super().__init__()
		self.daemon = True
		self.is_running = True
		self.notify_lock = threading.Event()
		self.name = 'observer_dummy'
	
	def notify(self):
		self.notify_lock.set()
	
	def stop(self):
		'''
		This is called by MainThread.
		'''
		self.is_running = False
		self.notify()
	
	def run(self):
		while self.is_running:
			self.notify_lock.clear()
			config.log.info('need to fetch things to show now.')
			self.notify_lock.wait()