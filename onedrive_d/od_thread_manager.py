#!/usr/bin/python3

"""
Thread Manager for onedrive_d
"""

import time
import socket
import threading
import queue
from . import od_glob

instance = None


def get_instance():
	global instance
	if instance == None:
		instance = NetworkingThreadManager()
		instance.start()
	return instance


class NetworkingThreadManager(threading.Thread):

	def __init__(self):
		super().__init__()
		self.name = 'thread_mgr'
		self.daemon = True
		self.sleep_queue = queue.Queue()
		self.conditions = {}
		self.logger = od_glob.get_logger()
		self.wait_interval = od_glob.get_config_instance(
			).params['NETWORK_ERROR_RETRY_INTERVAL']

	def hang_caller(self):
		"""
		Put whatever thread that calls this function to sleep.
		The ThreadManager thread must not call this function.
		"""
		self.conditions[
			threading.current_thread().ident] = cond = threading.Condition()
		self.sleep_queue.put(threading.current_thread())
		cond.acquire()
		self.logger.info('put to sleep due to networking error.')
		cond.wait()
		cond.release()
		self.logger.info('waken up by ThreadManager.')
		del self.conditions[threading.current_thread().ident]

	def is_connected(self, host_name='onedrive.com', host_port='80'):
		"""
		Test if the machine can reach the host:port.
		"""
		try:
			host_ip = socket.gethostbyname(host_name)
			s = socket.create_connection((host_ip, host_port), 1)
			s.shutdown(socket.SHUT_RDWR)
			s.close()
			self.logger.debug('able to realize "' + host_name + ':' + host_port + '".')
			return True
		except:
			self.logger.debug('cannot realize "' + host_name + ':' + host_port + '".')
		return False

	def run(self):
		self.logger.debug('started.')
		while True:
			t = self.sleep_queue.get()
			while not self.is_connected():
				time.sleep(self.wait_interval)
			self.conditions[t.ident].acquire()
			self.conditions[t.ident].notify()
			self.conditions[t.ident].release()

