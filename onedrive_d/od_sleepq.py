"""
Sleep queue for network I/O threads.
"""

import time
import socket
import threading
import queue
from . import od_bootstrap


instance = None

def get_instance(network_retry_interval=30):
	"""Sleep queue manager is a singleton"""
	global instance
	if instance is None:
		instance = SleepQueueManager(network_retry_interval)
		instance.start()
	return instance


class SleepQueueManager(threading.Thread):

	def __init__(self, network_retry_interval):
		super().__init__()
		self.name = 'sleepq'
		self.daemon = True
		self.sleep_queue = queue.Queue()
		self.conditions = {}
		self.logger = od_bootstrap.get_logger()
		self.wait_interval = network_retry_interval

	def hang_caller(self):
		"""
		Put whatever thread that calls this function to sleep.
		The ThreadManager thread must not call this function.
		"""
		self.conditions[
			threading.current_thread().ident] = cond = threading.Condition()
		self.sleep_queue.put(threading.current_thread())
		cond.acquire()
		self.logger.info('put to sleep due to network error.')
		cond.wait()
		cond.release()
		self.logger.info('waken up from sleep queue.')
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
			self.logger.debug('realized "' + host_name + ':' + host_port + '".')
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
