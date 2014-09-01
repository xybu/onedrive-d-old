#!/usr/bin/python3

"""
logger.py

The behavior of python built-in module `logging` is 
too complex for this use scenario so here is the simpler one.

@author	Xiangyu Bu <xybu92@live.com>

"""

from sys import stderr
from time import strftime
from threading import current_thread

class Logger:
	
	NOTSET = 0
	DEBUG = 10
	INFO = 20
	WARNING = 30
	ERROR = 40
	CRITICAL = 50
	
	VERSION = '1.0'
	
	def __init__(self, filepath = None, min_level = NOTSET):
		"""
		Initiate the logger object.
		
		@param filepath: if set, the log will be appended to this file; otherwise, use stderr instead.
		@param min_level: if set, logs whose levels are below it will be ignored.
		"""
		self._file = stderr
		self._min_level = min_level
		if filepath != None:
			try:
				self._file = open(filepath, 'a')
			except:
				self._file = stderr
				self.critical('Failed to open path "' + filepath + '" for logging. Use stderr instead.')
	
	def __del__(self):
		"""
		Close the file and free the memory
		"""
		if (self._file != stderr):
			self._file.close()
			del self._file
		del self
	
	def write(self, s):
		"""
		Write the string s to the log.
		"""
		print('[' + strftime('%c') + '] (' + current_thread().name + ')\t' + s, file = self._file)
	
	def debug(self, s):
		"""
		Write a debug log s.
		"""
		if self._min_level > Logger.DEBUG: return
		self.write('DEBUG: ' + s)
	
	def info(self, s):
		"""
		Write an info log s.
		"""
		if self._min_level > Logger.INFO: return
		self.write('INFO: ' + s)
	
	def warning(self, s):
		"""
		Write a warning log s.
		"""
		if self._min_level > Logger.WARNING: return
		self.write('WARNING: ' + s)
	
	def error(self, s):
		"""
		Write an error log s.
		"""
		if self._min_level > Logger.ERROR: return
		self.write('ERROR: ' + s)
	
	def critical(self, s):
		"""
		Write a critical log s.
		"""
		self.write('CRITICAL: ' + s)