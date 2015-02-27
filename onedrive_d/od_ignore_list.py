#!/usr/bin/python3

"""
onedrive-d ignore list implementation

The program works like a gitignore parser. 
Refer to http://git-scm.com/docs/gitignore

Notes:
 * Currently only support patterns like "*.swp", "path/to/*.swp", "\#swp#",
   "/path/*/*.swp", etc.
 * No '!' negation symbol support.
 * No '**' super matching support but single '*' is for super matching.
"""

import os
import fnmatch


class IgnoreList:

	def __init__(self, ignore_file_path, base_path):
		"""
		path: path to the ignore list file that is written according to Rules.
		"""
		f = open(ignore_file_path, 'r')
		t = f.read()
		f.close()
		lines = t.strip().split('\n')
		self.ignore_names = []
		self.ignore_paths = []
		for x in lines:
			x = x.strip()
			if not x.startswith('#') and x != '':
				if x.startswith('\\#'):
					x = x[1:]
				if x[-1] == '/':
					x = x + '*'  # this is ugly
				if '/' not in x:
					self.ignore_names.append(x)
				else:
					if x.startswith('/'):
						x = base_path + x
					else:
						x = '*/' + x
					self.ignore_paths.append(x)

	def is_ignorable(self, name, parent_path):
		for ign in self.ignore_names:
			if fnmatch.fnmatch(name, ign):
				return True

		name = parent_path + '/' + name
		for ign in self.ignore_paths:
			if fnmatch.fnmatch(name, ign):
				return True

		return False

	def filter_list(self, names, parent_path):
		"""
		Given a list of names and their parent path, return the list of names
		that should not be ignored.
		"""
		for ign in self.ignore_names:
			matched = fnmatch.filter(names, ign)
			for m in matched:
				names.remove(m)

		if len(self.ignore_paths) > 0:
			names_dup = [parent_path + '/' + n for n in names]
			for ign in self.ignore_paths:
				matched = fnmatch.filter(names_dup, ign)
				for m in matched:
					names.remove(os.path.basename(m))

		return names

	def __str__(self):
		dump = 'ignore_list:\n\tglob:\n'
		for x in self.ignore_names:
			dump = dump + '\t\t' + x + '\n'
		dump = dump + '\tpaths:\n'
		for x in self.ignore_paths:
			dump = dump + '\t\t' + x + '\n'
		return dump

