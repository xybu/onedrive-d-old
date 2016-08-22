#!/usr/bin/python3

"""
OneDrive REST API for onedrive_d.
Refer to http://msdn.microsoft.com/en-us/library/dn659752.aspx

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
import fcntl
# import imghdr
import requests
# for debugging
from time import sleep
from . import od_glob
from . import od_thread_manager
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
except:
	pass

api_instance = None


def get_instance():
	global api_instance
	if api_instance is None:
		api_instance = OneDriveAPI(od_glob.APP_CLIENT_ID, od_glob.APP_CLIENT_SECRET)
	return api_instance


class OneDriveAPIException(Exception):

	def __init__(self, args=None):
		super().__init__()
		if args is None:
			pass
		elif 'error_description' in args:
			self.errno = args['error']
			self.message = args['error_description']
		elif 'error' in args and 'code' in args['error']:
			args = args['error']
			self.errno = args['code']
			self.message = args['message']
		else:
			self.errno = 0
			self.message = ''

	def __str__(self):
		return self.message + ' (' + self.errno + ')'


class OneDriveAuthError(OneDriveAPIException):

	"""
	Raised when authentication fails.
	"""
	pass


class OneDriveServerInternalError(OneDriveAPIException):
	pass


class OneDriveValueError(OneDriveAPIException):

	"""
	Raised when input to OneDriveAPI is invalid.
	"""
	pass


class OneDriveAPI:

	CLIENT_SCOPE = ['wl.skydrive', 'wl.skydrive_update', 'wl.offline_access']
	REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'
	OAUTH_AUTHORIZE_URI = 'https://login.live.com/oauth20_authorize.srf?'
	OAUTH_TOKEN_URI = 'https://login.live.com/oauth20_token.srf'
	OAUTH_SIGNOUT_URI = 'https://login.live.com/oauth20_logout.srf'
	API_URI = 'https://apis.live.net/v5.0/'
	FOLDER_TYPES = ['folder', 'album']
	UNSUPPORTED_TYPES = ['notebook']
	ROOT_ENTRY_ID = 'me/skydrive'

	logger = od_glob.get_logger()
	threadman = od_thread_manager.get_instance()

	def __init__(self, client_id, client_secret, client_scope=CLIENT_SCOPE, redirect_uri=REDIRECT_URI):
		try:
			requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		except:
			pass
		self.client_access_token = None
		self.client_refresh_token = None
		self.client_id = client_id
		self.client_secret = client_secret
		self.client_scope = client_scope
		self.client_redirect_uri = redirect_uri
		self.http_client = requests.Session()

	def parse_response(self, request, error, ok_status=requests.codes.ok):
		ret = request.json()
		if request.status_code != ok_status:
			if 'code' in ret['error']:
				if ret['error']['code'] == 'request_token_expired':
					raise OneDriveAuthError(ret)
				elif ret['error']['code'] == 'server_internal_error':
					raise OneDriveServerInternalError(ret)
			raise error(ret)
		return ret

	def auto_recover_auth_error(self):
		"""
		Note that this function still throws exceptions.
		"""
		if self.client_refresh_token is None:
			raise OneDriveAuthError()
		refreshed_token_set = self.refresh_token(self.client_refresh_token)
		od_glob.get_config_instance().set_access_token(refreshed_token_set)
		self.logger.info('auto refreshed API token in face of auth error.')

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
		return OneDriveAPI.OAUTH_AUTHORIZE_URI + urllib.parse.urlencode(params)

	def is_signed_in(self):
		return self.access_token is not None

	def set_user_id(self, id):
		self.user_id = id

	def set_access_token(self, token):
		self.client_access_token = token
		self.http_client.headers.update({'Authorization': 'Bearer ' + token})

	def set_refresh_token(self, token):
		self.client_refresh_token = token

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
			raise OneDriveValueError(
				{'error': 'access_code_not_found', 'error_description': 'The access code is not specified.'})

		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"code": code,
			"grant_type": "authorization_code"
		}

		try:
			request = requests.post(
				OneDriveAPI.OAUTH_TOKEN_URI, data=params, verify=False)
			response = self.parse_response(request, OneDriveAPIException)
			self.set_access_token(response['access_token'])
			self.set_refresh_token(response['refresh_token'])
			self.set_user_id(response['user_id'])
			return response
		except requests.exceptions.ConnectionError as e:
			self.logger.exception(e);
			self.logger.info('network connection error.')
			self.threadman.hang_caller()
			return self.get_access_token(code, uri)

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
				request = requests.post(OneDriveAPI.OAUTH_TOKEN_URI, data=params, verify=False)
				response = self.parse_response(request, OneDriveAPIException)
				self.set_access_token(response['access_token'])
				self.set_refresh_token(response['refresh_token'])
				self.set_user_id(response['user_id'])
				return response
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def sign_out(self):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.OAUTH_SIGNOUT_URI + '?client_id=' + self.client_id + '&redirect_uri=' + self.client_redirect_uri, verify=False)
				return self.parse_response(r, OneDriveAuthError)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def get_recent_docs(self):
		raise NotImplementedError('get_recent_docs is not implemented.')

	def get_quota(self, user_id='me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id + '/skydrive/quota', verify=False)
				return self.parse_response(r, OneDriveAPIException)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def get_root_entry_name(self):
		return self.ROOT_ENTRY_ID

	def get_property(self, entry_id='me/skydrive'):
		try:
			r = self.http_client.get(OneDriveAPI.API_URI + entry_id, verify=False)
			return self.parse_response(r, OneDriveAPIException)
		except OneDriveAuthError:
			self.auto_recover_auth_error()
			return self.get_property(entry_id)
		except requests.exceptions.ConnectionError as e:
			self.logger.exception(e);
			self.logger.info('network connection error.')
			self.threadman.hang_caller()
			return self.get_property(entry_id)

	def set_property(self, entry_id, **kwargs):
		"""
		Different types of files have different RW fields.
		Refer to http://msdn.microsoft.com/en-us/library/dn631831.aspx.
		Example:
			self.set_property(your_id, name = 'new name', description = 'new desc')
		"""
		headers = {
			'Content-Type': 'application/json',
		}
		while True:
			try:
				r = self.http_client.put(
					OneDriveAPI.API_URI + entry_id, data=json.dumps(kwargs), headers=headers, verify=False)
				return self.parse_response(r, OneDriveAPIException)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def get_link(self, entry_id, type='r'):
		"""
		Return a link to share the entry.
		@param type: one of 'r' (default), 'rw', 'e' (short for 'embed').
		"""
		if type == 'r':
			type = 'shared_read_link'
		elif type == 'rw':
			type = 'shared_edit_link'
		else:
			type = 'embed'

		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/' + type, verify=False)
				return self.parse_response(r, OneDriveAPIException)['source']
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def list_entries(self, folder_id='me/skydrive', type='files'):
		"""
		@param type: 'files' (default) for all files. 'shared' for shared files (used internally).
		"""
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + folder_id + '/' + type, verify=False)
				return self.parse_response(r, OneDriveAPIException)['data']
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveServerInternalError as e:
				self.logger.error(e)
				self.threadman.hang_caller()

	def list_shared_entries(self, user_id='me'):
		return self.list_entries(user_id + '/skydrive', 'shared')

	def mkdir(self, folder_name, parent_id='me/skydrive'):
		if parent_id == '/':
			parent_id = 'me/skydrive'  # fix parent_id alias
		data = {'name': folder_name}
		headers = {'Content-Type': 'application/json'}
		uri = OneDriveAPI.API_URI + parent_id
		while True:
			try:
				r = self.http_client.post(uri, data=json.dumps(data), headers=headers, verify=False)
				return self.parse_response(r, OneDriveAPIException, requests.codes.created)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def cp(self, target_id, dest_folder_id, overwrite=True, type='COPY'):
		"""
		Return an entry dict if opeation succeeds.
		@param overwrite: whether or not to overwrite an existing entry. True, False, None (ChooseNewName).
		"""
		if overwrite is None:
			overwrite = 'ChooseNewName'
		data = {'destination': dest_folder_id}
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + self.client_access_token
		}
		uri = OneDriveAPI.API_URI + target_id + '?overwrite=' + str(overwrite)
		req = requests.Request(
			type, uri, data=json.dumps(data), headers=headers, verify=False).prepare()
		while True:
			try:
				r = self.http_client.send(req)
				return self.parse_response(r, OneDriveAPIException, requests.codes.created)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveServerInternalError as e:
				self.logger.error(e)
				self.threadman.hang_caller()

	def mv(self, target_id, dest_folder_id, overwrite=True):
		return self.cp(target_id, dest_folder_id, overwrite, 'MOVE')

	def bits_put(self, name, folder_id, local_path=None, block_size=1048576):
		"""
		Upload a large file with Microsoft BITS API.
		A detailed document: https://gist.github.com/rgregg/37ba8929768a62131e85
		Official document: https://msdn.microsoft.com/en-us/library/aa362821%28v=vs.85%29.aspx

		@param name: remote file name
		@param folder_id: the folder_id returned by Live API
		@param local_path: the local path of the file to upload
		@param remote_path (X): the remote path to put the file.

		@return None if an unrecoverable error occurs; or a file property dict.
		"""

		# get file size
		try:
			source_size = os.path.getsize(local_path)
		except:
			self.logger.error("cannot get file size of \"" + local_path + "\"")
			return None

		# produce request url
		if '!' in folder_id:
			# subfolder
			bits_folder_id = folder_id.split('.')[-1]
			url = "https://cid-" + self.user_id + \
				".users.storage.live.com/items/" + bits_folder_id + "/" + name
		elif folder_id != '':
			# root folder
			user_id = folder_id.split('.')[-1]
			url = "https://cid-" + user_id + \
				".users.storage.live.com/users/0x" + user_id + "/LiveFolders/" + name
		# elif remote_path is not None:
		# 	url = "https://cid-" + user_id + ".users.storage.live.com/users/0x" + user_id + "/LiveFolders/" + remote_path
		else:
			self.logger.error("cannot request BITS. folder_id is invalid.")
			return None

		# force refresh access token to get largest expiration time
		try:
			self.auto_recover_auth_error()
		except Exception as e:
			self.logger.error(e)
			return None

		# BITS: Create-Session
		headers = {
			'X-Http-Method-Override': 'BITS_POST',
			'Content-Length': '0',
			'BITS-Packet-Type': 'Create-Session',
			'BITS-Supported-Protocols': '{7df0354d-249b-430f-820d-3d2a9bef4931}'
		}
		self.logger.debug('getting session token for BITS upload...')
		while True:
			try:
				response = self.http_client.request('post', url, headers=headers, verify=False)
				if response.status_code != 201:
					if 'www-authenticate' in response.headers and 'invalid_token' in response.headers['www-authenticate']:
						response.close()
						raise OneDriveAuthError()
					else:
						# unknown error should be further analyzed
						self.logger.debug("failed BITS Create-Session request to upload \"%s\". HTTP %d.", local_path, response.status_code)
						self.logger.debug(response.headers)
						response.close()
						return None
				session_id = response.headers['bits-session-id']
				response.close()
				break
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
		del headers

		# BITS: upload file by blocks
		# The autnentication of this part relies on session_id, not access_token.
		self.logger.debug('uploading file "%s".', local_path)
		source_file = open(local_path, 'rb')
		fcntl.lockf(source_file, fcntl.LOCK_SH)
		source_cursor = 0
		while source_cursor < source_size:
			try:
				target_cursor = min(source_cursor + block_size, source_size) - 1
				source_file.seek(source_cursor)
				data = source_file.read(target_cursor - source_cursor + 1)
				self.logger.debug("uploading block %d - %d (total: %d B)", source_cursor, target_cursor, source_size)
				response = self.http_client.request('post', url, data=data, headers={
					'X-Http-Method-Override': 'BITS_POST',
					'BITS-Packet-Type': 'Fragment',
					'BITS-Session-Id': session_id,
					'Content-Range': 'bytes {}-{}/{}'.format(source_cursor, target_cursor, source_size)
				}, verify=False)
				if response.status_code != requests.codes.ok:
					# unknown error. better log it for future analysis
					self.logger.debug('an error occurred uploading the block. HTTP %d.', response.status_code)
					self.logger.debug(response.headers)
					response.close()
					fcntl.lockf(source_file, fcntl.LOCK_UN)
					source_file.close()
					# should I cancel session? https://msdn.microsoft.com/en-us/library/aa362829%28v=vs.85%29.aspx
					return None
				else:
					source_cursor = int(response.headers['bits-received-content-range'])
					response.close()
					del data
					# sleep(1)
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				del data
				self.threadman.hang_caller()
		fcntl.lockf(source_file, fcntl.LOCK_UN)
		source_file.close()

		# refresh token if expired
		if od_glob.get_config_instance().is_token_expired():
			try:
				self.auto_recover_auth_error()
			except Exception as e:
				# this branch is horrible
				self.logger.error(e)
				return None

		# BITS: close session
		self.logger.debug('BITS upload completed. Closing session...')
		headers = {
			'X-Http-Method-Override': 'BITS_POST',
			'BITS-Packet-Type': 'Close-Session',
			'BITS-Session-Id': session_id,
			'Content-Length': '0'
		}
		while True:
			try:
				response = self.http_client.request('post', url, headers=headers, verify=False)
				if response.status_code != requests.codes.ok and response.status_code != requests.codes.created:
					# when token expires, server return HTTP 500
					# www-authenticate: 'Bearer realm="OneDriveAPI", error="expired_token", error_description="Auth token expired. Try refreshing."'
					if 'www-authenticate' in response.headers and 'expired_token' in response.headers['www-authenticate']:  # 'invalid_token' in response.headers['www-authenticate']:
						response.close()
						raise OneDriveAuthError()
					else:
						# however, when the token is changed,
						# we will get HTTP 500 with 'x-clienterrorcode': 'UploadSessionNotFound'
						self.logger.debug('An error occurred when closing BITS session. HTTP %d', response.status_code)
						self.logger.debug(response.headers)
						response.close()
						return None
				res_id = response.headers['x-resource-id']
				response.close()
				self.logger.debug('BITS session successfully closed.')
				return self.get_property('file.' + res_id[:res_id.index('!')] + '.' + res_id)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def put(self, name, folder_id='me/skydrive', upload_location=None, local_path=None, data=None, overwrite=True):
		"""
		Upload the file or data to a path.
		Returns a dict with keys 'source', 'name', and 'id'

		@param name: the new name used for the uploaded FILE. Assuming the name is NTFS-compatible.
		@param folder_id: the parent folder of the entry to upload. Default: root folder.
		@param upload_location: OneDrive upload_location URL. If given, folder_id is ignored.
		@param local_path: the local path of the FILE.
		@param data: the data of the entry. If given, local_path is ignored.
		@param overwrite: whether or not to overwrite existing files, if any.

		To put an empty file, either local_path points to an empty file or data is set ''.
		To upload a dir, check if it exists, and then send recursive puts to upload its files.

		Another issue is timestamp correction.
		"""
		uri = OneDriveAPI.API_URI
		if upload_location is not None:
			uri += upload_location  # already ends with '/'
		else:
			uri += folder_id + '/files/'

		if name == '':
			raise OneDriveValueError(
				{'error': 'empty_name', 'error_description': 'The file name cannot be empty.'})
		uri += name

		d = {
			'downsize_photo_uploads': False,
			'overwrite': overwrite
		}
		uri += '?' + urllib.parse.urlencode(d)

		if data is not None:
			pass
		elif local_path is not None:
			if not os.path.isfile(local_path):
				raise OneDriveValueError(
					{'error': 'wrong_file_type', 'error_description': 'The local path "' + local_path + '" is not a file.'})
			else:
				data = open(local_path, 'rb')
		else:
			raise OneDriveValueError(
				{'error': 'upload_null_content', 'error_description': 'local_path and data cannot both be null.'})

		while True:
			try:
				r = self.http_client.put(uri, data=data, verify=False)
				ret = r.json()
				if r.status_code != requests.codes.ok and r.status_code != requests.codes.created:
					# TODO: try testing this
					if 'error' in ret and 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired':
						raise OneDriveAuthError(ret)
					else:
						raise OneDriveAPIException(ret)
				return self.get_property(ret['id'])
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveServerInternalError as e:
				self.logger.error(e)
				self.threadman.hang_caller()

	def get_by_blocks(self, entry_id, local_path, file_size, block_size):
		try:
			f = open(local_path, 'wb')
		except OSError as e:
			self.logger.error(e)
			return False
		self.logger.debug('download file to "' + local_path + '"...')
		# fcntl.lockf(f, fcntl.LOCK_SH)
		cursor = 0
		while cursor < file_size:
			self.logger.debug('current cursor: ' + str(cursor))
			try:
				target = min(cursor + block_size, file_size) - 1
				r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/content',
					headers={
						'Range': 'bytes={0}-{1}'.format(cursor, target)
					}, verify=False)
				if r.status_code == requests.codes.ok or r.status_code == requests.codes.partial:
					# sample data: 'bytes 12582912-12927920/12927921'
					range_unit, range_str = r.headers['content-range'].split(' ')
					range_range, range_total = range_str.split('/')
					range_from, range_to = range_range.split('-')
					f.write(r.content)
					cursor = int(range_to) + 1
					r.close()
				else:
					if 'www-authenticate' in r.headers and 'invalid_token' in r.headers['www-authenticate']:
						raise OneDriveAuthError()
					else:
						self.logger.debug('failed downloading block. HTTP %d.', r.status_code)
						self.logger.debug(r.headers)
						self.logger.debug(r.content)
						return False
					# return False
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
		f.close()
		self.logger.debug('file saved.')
		# fcntl.lockf(f, fcntl.LOCK_UN)
		return True

	def get_size(self, entry_id):
		r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/content', verify=False)
		self.logger.info('filesize ' + entry_id + ' size is: ' + r.headers['content-length'])
	
	def get(self, entry_id, local_path=None):
		"""
		Fetching content of OneNote files will raise OneDriveAPIException:
		Resource type 'notebook' doesn't support the path 'content'. (request_url_invalid)
		"""
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/content', verify=False)
				if r.status_code != requests.codes.ok:
					ret = r.json()
					# TODO: try testing this
					if 'error' in ret and 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired':
						raise OneDriveAuthError(ret)
					else:
						raise OneDriveAPIException(ret)
				if local_path is not None:
					with open(local_path, 'wb') as f:
						f.write(r.content)
					return True
				else:
					return r.content
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveServerInternalError as e:
				self.logger.error(e)
				self.threadman.hang_caller()

	def rm(self, entry_id):
		"""
		OneDrive API always returns HTTP 204.
		"""
		while True:
			try:
				self.http_client.delete(OneDriveAPI.API_URI + entry_id, verify=False)
				return
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
			except OneDriveServerInternalError as e:
				self.logger.error(e)
				self.threadman.hang_caller()

	def get_user_info(self, user_id='me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id, verify=False)
				return self.parse_response(r, OneDriveAPIException, requests.codes.ok)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()

	def get_contact_list(self, user_id='me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id + '/friends', verify=False)
				return self.parse_response(r, OneDriveAPIException, requests.codes.ok)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError as e:
				self.logger.exception(e);
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
