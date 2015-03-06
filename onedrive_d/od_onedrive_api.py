#!/usr/bin/python3

"""
New OneDrive API as described in http://onedrive.github.io.

Notes:

 * The API object can be called by any arbitrary thread in the program.
 * Call get_instance() will realize a API singleton object.
 * When there is network issue at an API call, the calling thread is put to sleep
   and thread manager will wake it up when the network seems fine. When the caller
   is waken up, it will retry the function that failed before.
 * When refresh_token is set, API will try to get new access_token automatically
   and retry the function call later.

Bullets 3 and 4 are like interrupt handling.
"""

import os
import json
import urllib
import functools
import requests
import portalocker
from time import sleep
from . import od_glob
from . import od_thread_manager
from . import od_objects

api_instance = None


def get_instance():
	global api_instance
	if api_instance is None:
		api_instance = OneDriveAPI(od_glob.APP_CLIENT_ID, od_glob.APP_CLIENT_SECRET)
	return api_instance


class OneDriveError(Exception):
	"""
	New format of OneDrive error responses.
	"""
	def __init__(self, error_response):
		super().__init__(self)
		self.message = error_response['message']
		self.errno = error_response['code']
		if 'innererror' in error_response:
			self.inner_error = error_response['innererror']

	def __str__(self):
		return self.message + ' (' + self.errno + ')'


class OneDriveRecoveredError(Exception):
	pass


class OneDriveAuthError(OneDriveError):
	pass


class OneDriveConflictError(OneDriveError):
	pass


class OneDriveValueError(OneDriveError):
	"""
	Raised when input to OneDriveAPI is invalid.
	"""
	pass


class OneDriveAPI:
 
	# API_URI = 'https://apis.live.net/v5.0/'
	FOLDER_TYPES = ['folder', 'album']
	UNSUPPORTED_TYPES = ['notebook']
	ROOT_ENTRY_ID = 'me/skydrive'

	client_scope = ['onedrive.readwrite', 'wl.offline_access']
	client_redirect_uri = 'https://login.live.com/oauth20_desktop.srf'
	oauth_signin_url = 'https://login.live.com/oauth20_authorize.srf?'
	oauth_signout_url = 'https://login.live.com/oauth20_logout.srf'
	oauth_token_url = 'https://login.live.com/oauth20_token.srf'
	api_url = 'https://api.onedrive.com/v1.0'
	logger = od_glob.get_logger()
	config = od_glob.get_config_instance()
	threadman = od_thread_manager.get_instance()
	created_status_code = [requests.codes.created, requests.codes.ok]
	json_type_header = {'Content-Type': 'application/json'}

	def __init__(self, client_id, client_secret, client_scope=None, redirect_uri=None):
		self.client_access_token = None
		self.client_refresh_token = None
		self.client_id = client_id
		self.client_secret = client_secret
		if client_scope is not None:
			self.client_scope = client_scope
		if redirect_uri is not None:
			self.client_redirect_uri = redirect_uri
		self.http_client = requests.Session()

	def raise_error(self, request):
		if request.status_code == requests.codes.too_many_requests:
			sleep(int(request.headers['retry-after']))
			raise OneDriveRecoveredError()
		elif 'www-authenticate' in request.headers and 'expired_token' in request.headers['www-authenticate']:
			self.recover_auth_error()
			raise OneDriveRecoveredError()
		else:
			error = request.json()
			raise OneDriveError(error['error'])

	def recover_auth_error(self):
		"""
		Note that this function still throws exceptions.
		"""
		if self.client_refresh_token is None:
			raise OneDriveAuthError()
		new_tokens = self.refresh_token(self.client_refresh_token)
		self.config.set_access_token(new_tokens)
		self.logger.info('auto refreshed API token in face of auth error.')

	def load_tokens(self, tokens):
		self.user_id = tokens['user_id']
		self.client_access_token = tokens['access_token']
		self.client_refresh_token = tokens['refresh_token']
		self.http_client.headers.update({'Authorization': 'Bearer ' + tokens['access_token']})

	def expand_res_url(self, drive_id, item_id, item_path):
		if item_id is not None:
			url = '/items/' + item_id
		else:
			url = '/root'
			if item_path is not None:
				url = url + ':/' + item_path
		if drive_id is not None:
			url = '/drives/' + drive_id + url
		else:
			url = '/drive' + url
		return url

	def str_to_range(self, r, maxsize):
		if r[-1] == '-':
			return (int(r[:-1]), maxsize)
		else:
			r2 = r.split('-')
			start = int(r2[0])
			end = int(r2[1])
			return (start, end)

	def get_auth_uri(self, display='touch', locale='en', state=''):
		"""
		Use the code returned in the final redirect URL to exchange for
		an access token

		http://msdn.microsoft.com/en-us/library/dn659750.aspx
		"""
		params = {
			'client_id': self.client_id,
			'scope': ' '.join(self.client_scope),
			'response_type': 'code',
			'redirect_uri': self.client_redirect_uri,
			'display': display,
			'locale': locale
		}
		if state != '':
			params['state'] = state
		return self.oauth_signin_url + urllib.parse.urlencode(params)

	def get_access_token(self, code=None, uri=None):
		"""
		http://msdn.microsoft.com/en-us/library/dn659750.aspx

		return a dict with keys token_type, expires_in, scope,
		access_token, refresh_token, authentication_token
		"""
		if uri is not None and '?' in uri:
			qs_dict = urllib.parse.parse_qs(uri.split('?')[1])
			if 'code' in qs_dict:
				code = qs_dict['code']
		if code is None:
			raise OneDriveValueError({'code': 'auth_code_not_found', 'message': 'The auth code is not specified.'})

		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"code": code,
			"grant_type": "authorization_code"
		}

		while True:
			try:
				response = requests.post(self.oauth_token_url, data=params, verify=True)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				tokens = response.json()
				self.load_tokens(tokens)
				return tokens
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def refresh_token(self, token):
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"refresh_token": token,
			"grant_type": 'refresh_token'
		}
		while True:
			try:
				response = requests.post(self.oauth_token_url, data=params)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				tokens = response.json()
				self.load_tokens(tokens)
				return tokens
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def sign_out(self):
		while True:
			try:
				self.http_client.get(self.oauth_signout_url + '?client_id=' + self.client_id + '&redirect_uri=' + self.client_redirect_uri)
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def get_all_drives_meta(self):
		"""
		List all Drives available to the authenticated user.
		"""
		while True:
			try:
				response = self.http_client.get(self.api_url + '/drives')
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				data = response.json()
				drives = {}
				for v in data['value']:
					d = od_objects.DriveObject(v)
					drives[d.id] = d
				return drives
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def get_drive_meta(self, drive_id=None):
		"""
		Use default drive when drive_id is None.
		"""
		url = self.api_url + '/drive'
		if drive_id is not None:
			url = url + 's/' + drive_id
		while True:
			try:
				response = self.http_client.get(url)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				return od_objects.DriveObject(response.json())
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def get_item(self, drive_id=None, item_id=None, item_path=None, children=None):
		"""
		When drive_id is None, get root folder of user's default Drive.
		item_id is preferred is preferred over item_path.
		When both item_id and item_path are None, return info about root.
		<del>If etag is provided, HTTP 304 Not Mofified can be returned.</del>
		children is one of None, 'expand', 'only'.

		Should support more params: http://onedrive.github.io/odata/optional-query-parameters.htm
		"""
		url = self.expand_res_url(drive_id, item_id, item_path)
		if children is not None:
			if children[0] == 'e':
				url = url + '?expand=children'
			elif children[0] == 'o':
				if item_id is not None:
					url = url + '/children'
				else:
					url = url + ':/children'
		while True:
			try:
				response = self.http_client.get(self.api_url + url)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				data = response.json()
				# with open('dump', 'w') as f:
				# 	json.dump(data, f)
				if children is None or children[0] != 'o':
					return od_objects.ItemObject(data)
				else:
					return od_objects.make_item_collection(data['value'])
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def create_dir(self, name, drive_id=None, parent_id=None, parent_path=None, conflict='rename'):
		"""
		conflict must be in ['rename', 'replace', 'fail']
		http://onedrive.github.io/items/create.htm
		"""
		url = self.expand_res_url(drive_id, parent_id, parent_path)
		if parent_id is not None:
			url = url + '/children'
		else:
			url = url + ':/children'
		d = {'name': name, 'folder': {}, '@name.conflictBehavior': conflict}
		while True:
			try:
				response = self.http_client.post(self.api_url + url, data=json.dumps(d), headers=self.json_type_header)
				if response.status_code != requests.codes.created:
					# print(response.text)
					self.raise_error(response)
				return od_objects.SimpleItemObject(response.json())
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def put_file(self, filename, filepath, drive_id=None, parent_id=None, parent_path=None):
		"""
		Does this API shrink image?
		Raises OSError
		http://onedrive.github.io/items/upload_put.htm
		"""
		url = self.expand_res_url(drive_id, parent_id, parent_path)
		if parent_id is not None:
			url = url + '/children/' + filename + '/content'
		else:
			url = url + '/' + filename + ':/content'
		# if not os.path.isfile(filepath)
		# assume path is correct
		with open(filepath, 'rb') as f:
			url = self.api_url + url
			# print(url)
			portalocker.lock(f, portalocker.LOCK_EX)
			while True:
				try:
					response = self.http_client.put(url, data=f)
					if response.status_code not in self.created_status_code:
						self.raise_error(response)
					return od_objects.ItemObject(response.json())
				except requests.exceptions.ConnectionError:
					self.logger.info('network connection error.')
					self.threadman.hang_caller()
				except OneDriveRecoveredError:
					pass

	def put_by_url(self):
		"""
		OneDrive API not available yet.
		http://onedrive.github.io/items/upload_url.htm
		"""
		raise NotImplementedError()

	def get_upload_session(self, filename, drive_id=None, parent_id=None, parent_path=None, conflict='rename', resume_url=None):
		if resume_url is not None:
			# get session from resume_url
			while True:
				try:
					response = self.http_client.get(resume_url)
					if response.status_code == requests.codes.not_found:
						# leave session None so a new one can be created
						break
					elif response.status_code != requests.codes.ok:
						self.raise_error(response)
					session = response.json()
					session['uploadUrl'] = resume_url
					return session
				except requests.exceptions.ConnectionError:
					self.logger.info('network connection error.')
					self.threadman.hang_caller()
				except OneDriveRecoveredError:
					pass
		url = self.expand_res_url(drive_id, parent_id, parent_path)
		if parent_id is not None:
			url = url + ':'
		url = url + '/' + filename
		d = {'@name.conflictBehavior': conflict}
		while True:
			try:
				response = self.http_client.post(self.api_url + url + ':/upload.createSession', data=json.dumps(d), headers=self.json_type_header)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				return response.json()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def abort_upload_session(self, session):
		try:
			self.http_client.delete(session['uploadUrl'])
		except:
			pass

	def upload_file(self, filepath, session, blocksize=655360):
		"""
		conflict must be in ['rename', 'replace', 'fail']
		Raises:
			OSError, OneDriveConflictError
		Warning:
			conflicts created during uploading needs handling manually.
		Known bugs:
			#7 API does not handle conflict="replace" (https://github.com/OneDrive/onedrive-api-docs/issues/7).
		http://onedrive.github.io/items/upload_large_files.htm
		"""
		filesize = os.path.getsize(filepath)
		range_queue = []
		for r in session['nextExpectedRanges']:
			range_queue.append(self.str_to_range(r, filesize))
		with open(filepath, 'rb') as f:
			portalocker.lock(f, portalocker.LOCK_EX)
			while len(range_queue) > 0:
				start, end = range_queue[0]
				del range_queue[0]
				f.seek(start)
				if end - start > blocksize:
					end = start + blocksize - 1
				elif end == filesize:
					end = filesize - 1
				rstr = 'bytes {0}-{1}/{2}'.format(start, end, filesize)
				d = f.read(end - start + 1)
				h = {'Content-Range': rstr}
				attempt = 0
				while True:
					attempt = attempt + 1
					self.logger.debug('%d attempt uploading "%s": %s.', attempt, filepath, rstr)
					try:
						response = self.http_client.put(session['uploadUrl'], data=d, headers=h)
						if response.status_code != requests.codes.accepted:
							# print(response.headers)
							# print(response.json())
							if response.status_code in self.created_status_code:
								# file has been created
								assert len(range_queue) == 0, 'server creates the file before queue gets emptied.'
								js = response.json()
								obj = od_objects.ItemObject(js)
								obj.set_parent_ref(js['parentReference'])
								return obj
							elif response.status_code == requests.codes.conflict:
								assert len(range_queue) == 0, 'server creates the file before queue gets emptied.'
								raise OneDriveConflictError(response.json()['error'])
							# don't know how quota overlimit returns
							else:
								self.raise_error(response)
						j = response.json()
						if 'nextExpectedRanges' in j:
							for r in j['nextExpectedRanges']:
								range_queue.append(self.str_to_range(r, filesize))
						else:
							range_queue.append((end + 1, filesize))
						break
					except requests.exceptions.ConnectionError:
						self.logger.info('network connection error.')
						self.threadman.hang_caller()
					except OneDriveRecoveredError:
						pass
				del d

	def handle_session_conflict(self, filename, source_url, drive_id=None, parent_id=None, parent_path=None, conflict='rename'):
		"""
		Raises: 
			OneDriveError: 
				The name in the provided oneDrive.item does not match the name in the URL (invalidArgument)
					Raised even when source_url is session's uploadUrl.
		"""
		url = self.expand_res_url(drive_id, parent_id, parent_path)
		d = {
			'name': filename,
			'@name.conflictBehavior': conflict,
			'@content.sourceUrl': source_url
		}
		while True:
			try:
				response = self.http_client.put(self.api_url + url, data=json.dumps(d), headers=self.json_type_header)
				if response.status_code not in self.created_status_code:
					self.raise_error(response)
				return od_objects.ItemObject(response.json())
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def patch_item(self, drive_id=None, item_id=None, item_path=None, new_name=None, new_parent_ref=None):
		"""
		If new_parent_ref is manually constructed, the 'path' field, if used, should be 
		expanded by expand_res_url to make a form like /drive/root:/foo_dir/bar_dir'

		This function call works as "move" when new_name is None and new_parent_ref is not None.
		"""
		if new_name is None and new_parent_ref is None:
			raise OneDriveValueError({'code': 'invalid_call', 'message': 'there is nothing to do.'})
		url = self.expand_res_url(drive_id, item_id, item_path)
		d = {}
		if new_name is not None:
			d['name'] = new_name
		if new_parent_ref is not None:
			d['parentReference'] = new_parent_ref.__dict__
		while True:
			try:
				response = self.http_client.patch(self.api_url + url, data=json.dumps(d), headers=self.json_type_header)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				return od_objects.ItemObject(response.json())
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def delete_item(self, drive_id=None, item_id=None, item_path=None):
		url = self.expand_res_url(drive_id, item_id, item_path)
		while True:
			try:
				response = self.http_client.delete(self.api_url + url)
				if response.status_code != requests.codes.no_content:
					self.raise_error(response)
				return
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def copy_item(self, drive_id=None, item_id=None, item_path=None, new_name=None, new_parent_ref=None, async=True):
		"""
		Return a URL that can be used to track the progress of copy action.
		Warnings:
			Cannot copy to root with 'path': '/drive/root:'.
			Currently async must be True.
		"""
		if new_parent_ref is None:
			raise OneDriveValueError({'code': 'invalid_call', 'message': 'unknown copy dest.'})
		url = self.expand_res_url(drive_id, item_id, item_path)
		if item_path is not None:
			url = url + ':'
		url = url + '/action.copy'
		d = {}
		if new_name is not None:
			d['name'] = new_name
		if new_parent_ref is not None:
			d['parentReference'] = new_parent_ref.__dict__
		headers = self.json_type_header.copy()
		if async:
			headers['Prefer'] = 'respond-async'
		while True:
			try:
				response = self.http_client.post(self.api_url + url, data=json.dumps(d), headers=headers)
				if response.status_code != requests.codes.accepted:
					self.raise_error(response)
				return response.headers['location']
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def get_url(self, url):
		while True:
			try:
				response = self.http_client.get(url)
				# print(response.status_code)
				# print(response.headers)
				# print(response.content)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				return response.content
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def wait_copy_done(self, url, interval=1):
		"""
		Expect huge waiting time before the request is fulfilled.
		"""
		while True:
			try:
				response = self.http_client.get(url)
				if response.status_code != requests.codes.see_other:
					if response.status_code == requests.codes.accepted:
						js = response.json()
						# print(js)
						if js['status'] == 'NotStarted':
							sleep(30 * interval)
						else:
							sleep(interval)
						raise OneDriveRecoveredError()
					else:
						self.raise_error(response)
				content = self.get_url(response.headers['location'])
				return od_objects.ItemObject(content)
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def save_url_to_file(self, filepath, url):
		content = self.get_url(url)
		with open(filepath, 'wb') as f:
			portalocker.lock(f, portalocker.LOCK_EX)
			f.write(content)

	def get_file(self, filepath, drive_id=None, item_id=None, item_path=None, etag=None):
		"""
		Currently etag is not implemented yet.
		Don't forget to fix timestamps.
		"""
		url = self.expand_res_url(drive_id, item_id, item_path)
		if item_path is not None:
			url = url + ':'
		url = self.api_url + url + '/content'
		while True:
			try:
				response = self.http_client.get(url)
				# print(response.status_code)
				# print(response.headers)
				# print(response.content)
				if response.status_code == requests.codes.ok:
					with open(filepath, 'wb') as f:
						f.write(response.content)
					return
				elif response.status_code == requests.codes.found:
					return self.save_url_to_file(filepath, response.headers['location'])
				else:
					self.raise_error(response)
				# print('wtf')
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass

	def get_file_by_blocks(self, filepath, filesize, drive_id=None, item_id=None, item_path=None, blocksize=655360):
		url = self.expand_res_url(drive_id, item_id, item_path)
		if item_path is not None:
			url = url + ':'
		url = self.api_url + url + '/content'
		with open(filepath, 'wb') as wf:
			portalocker.lock(wf, portalocker.LOCK_EX)
			start = 0
			while start < filesize:
				# self.logger.debug('%d / %d.', start, filesize)
				end = min(start + blocksize, filesize) - 1
				rstr = 'bytes={0}-{1}'.format(start, end)
				h = {'range': rstr}
				attempt = 0
				while True:
					attempt = attempt + 1
					self.logger.debug('%d attempt downloading "%s": %s.', attempt, filepath, rstr)
					try:
						response = self.http_client.get(url, headers=h)
						# print(response.status_code)
						# print(response.headers)
						# print(response.content)
						if response.status_code == requests.codes.partial:
							wf.write(response.content)
							start = start + int(response.headers['content-length'])
							break
						elif response.status_code == requests.codes.found:
							content = self.get_url(response.headers['location'])
							wf.write(content)
							start = start + int(response.headers['content-length'])
							break
						else:
							# print(response.content)
							self.raise_error(response)
						# print('wtf')
					except requests.exceptions.ConnectionError:
						self.logger.info('network connection error.')
						self.threadman.hang_caller()
					except OneDriveRecoveredError:
						pass

	def search_item(self):
		"""
		API still in preview status. Don't bother implementing.
		"""
		raise NotImplementedError()

	def view_changes(self, drive_id=None, item_id=None, item_path=None, token=None):
		"""
		This API is not very useful given what onedrive-d has.
		Will consider later.
		"""
		url = self.expand_res_url(drive_id, item_id, item_path)
		if item_path is not None:
			url = url + ':'
		url = self.api_url + url + '/view.changes'
		if token is not None:
			url = url + '?token=' + token
		while True:
			try:
				response = self.http_client.get(url)
				# print(response.status_code)
				# print(response.headers)
				# print(response.content)
				with open('view_changes.js', 'wb') as f:
					f.write(response.content)
				if response.status_code != requests.codes.ok:
					self.raise_error(response)
				js = response.json()
				return js
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveRecoveredError:
				pass
