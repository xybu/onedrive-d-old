#!/usr/bin/python3

from . import od_glob


def make_item_collection(js):
	children_set = {}
	if len(js) > 0:
		parent_ref = ParentReference(js[0]['parentReference'])
		for c in js:
			if 'parentReference' in c:
				del c['parentReference']
			obj = ItemObject(c)
			obj.parent_ref = parent_ref
			children_set[obj.name] = obj
	return children_set


class UserIdentity:
	"""
	Attributes: display_name, id
	"""

	def __init__(self, js):
		self.display_name = js['displayName']
		self.id = js['id']

	def __str__(self):
		return self.display_name + '(' + self.id + ')'


class AsyncOperationStatus:
	"""
	Not used yet.
	Attributes:
		operation, 
		percentageComplete, 
		status: 
				NotStarted | inProgress | completed | updating | failed | 
				deletePending | deleteFailed | waiting
	"""
	def __init__(self, js):
		self.__dict__.update(js)

	def __str__(self):
		return str(self.__dict__)


class QuotaInfo:
	"""
	Attributes: used, deleted, remaining, total, state
	"""
	def __init__(self, js):
		self.__dict__.update(js)

	def __str__(self):
		return str(self.__dict__)


class DriveObject:

	def __init__(self, js):
		self.id = js['id']
		self.drive_type = js['driveType']
		self.quota = QuotaInfo(js['quota'])

	def __str__(self):
		return 'Drive ' + self.id + ' (' + self.drive_type + ')'


class ParentReference:
	"""
	Attributes: id, path, driveId (not drive_id!)
	"""
	def __init__(self, js):
		self.__dict__.update(js)

	def __str__(self):
		return '(%(driveId)s, %(id)s, %(path)s)' % self.__dict__


class SimpleItemObject:

	def __init__(self, js):
		self.id = js['id']
		self.name = js['name']
		self.is_folder = 'folder' in js


class ItemObject(SimpleItemObject):

	def __init__(self, js):
		# print(js)
		super().__init__(js)
		self.etag = js['eTag']
		# self.ctag = js['cTag']
		# self.created_by
		self.created_time = od_glob.str_to_time(js['createdDateTime'])
		self.modified_time = od_glob.str_to_time(js['lastModifiedDateTime'])
		# if 'user' in js['lastModifiedBy']:
		# 	self.last_modified_by = UserInfo(js['lastModifiedBy']['user'])
		self.size = js['size']
		if self.is_folder:
			self.child_count = js['folder']['childCount']
			if 'children' in js:
				self.children = make_item_collection(js['children'])
			if 'specialFolder' in js:
				self.is_special = True
				self.special_name = js['specialFolder']['name']
			else:
				self.is_special = False
		else:
			if 'file' in js:
				if 'crc32Hash' in js['file']['hashes']:
					self.file_hash_type = 'crc32'
					self.file_hash = js['file']['hashes']['crc32Hash']
				elif 'sha1Hash' in js['file']['hashes']:
					self.file_hash_type = 'sha1'
					self.file_hash = js['file']['hashes']['sha1Hash']
				else:
					self.file_hash_type = None	
			else:
				self.file_hash_type = None
			if '@content.downloadUrl' in js:
				self.download_url = js['@content.downloadUrl']
			# self.file_mime = js['file']['mimeType']
		if 'parentReference' in js:
			self.parent_ref = ParentReference(js['parentReference'])


	def __str__(self):
		return str(self.__dict__)
