#!/usr/bin/python3

'''
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
'''

import os
import json
import urllib
import imghdr
import requests
import od_glob
import od_thread_manager

api_instance = None

def get_instance():
	global api_instance
	if api_instance == None:
		api_instance = OneDriveAPI(od_glob.APP_CLIENT_ID, od_glob.APP_CLIENT_SECRET)
	return api_instance

class OneDriveAPIException(Exception):
	def __init__(self, args = None):
		super().__init__()
		if 'error_description' in args:
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
	'''
	Raised when authentication fails.
	'''
	pass
	
class OneDriveValueError(OneDriveAPIException): 
	'''
	Raised when input to OneDriveAPI is invalid.
	'''
	pass

class OneDriveAPI:
	
	CLIENT_SCOPE = ['wl.skydrive', 'wl.skydrive_update', 'wl.offline_access']
	REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'
	OAUTH_AUTHORIZE_URI = 'https://login.live.com/oauth20_authorize.srf?'
	OAUTH_TOKEN_URI = 'https://login.live.com/oauth20_token.srf'
	OAUTH_SIGNOUT_URI = 'https://login.live.com/oauth20_logout.srf'
	API_URI = 'https://apis.live.net/v5.0/'
	FOLDER_TYPES = ['folder', 'album']
	
	def __init__(self, client_id, client_secret, client_scope = CLIENT_SCOPE, redirect_uri = REDIRECT_URI):
		self.client_access_token = None
		self.client_refresh_token = None
		self.client_id = client_id
		self.client_secret = client_secret
		self.client_scope = client_scope
		self.client_redirect_uri = redirect_uri
		self.http_client = requests.Session()
		self.threadman = od_thread_manager.get_instance()
		self.logger = od_glob.get_logger()
	
	def parse_response(self, request, error, ok_status = requests.codes.ok):
		ret = request.json()
		if request.status_code != ok_status:
			if 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired':
				raise OneDriveAuthError(ret)
			else: raise error(ret)
		return ret
	
	def auto_recover_auth_error(self):
		if self.client_refresh_token == None: raise OneDriveAuthError()
		refreshed_token_set = self.refresh_token(self.client_refresh_token)
		od_glob.get_config_instance().set_access_token(refreshed_token_set)
	
	def get_auth_uri(self, display = 'touch', locale = 'en', state = ''):
		'''
		Use the code returned in the final redirect URL to exchange for
		an access token
		
		http://msdn.microsoft.com/en-us/library/dn659750.aspx
		'''
		params = {
			'client_id': self.client_id,
			'scope': ' '.join(self.client_scope),
			'response_type': 'code',
			'redirect_uri': self.client_redirect_uri,
			'display': display,
			'locale': locale
		}
		if state != '': params['state'] = state
		return OneDriveAPI.OAUTH_AUTHORIZE_URI + urllib.parse.urlencode(params)
	
	def is_signed_in(self):
		return self.access_token != None
	
	def set_access_token(self, token):
		self.client_access_token = token
		self.http_client.headers.update({'Authorization': 'Bearer ' + token})
	
	def set_refresh_token(self, token):
		self.client_refresh_token = token
	
	def get_access_token(self, code = None, uri = None):
		'''
		http://msdn.microsoft.com/en-us/library/dn659750.aspx
		
		return a dict with keys token_type, expires_in, scope, 
		access_token, refresh_token, authentication_token
		'''
		if uri != None and '?' in uri:
			qs_dict = urllib.parse.parse_qs(uri.split('?')[1])
			if 'code' in qs_dict: code = qs_dict['code']
		if code == None:
			raise OneDriveValueError({'error': 'access_code_not_found', 'error_description': 'The access code is not specified.'})
		
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"code": code,
			"grant_type": "authorization_code"
		}
		
		try:
			request = requests.post(OneDriveAPI.OAUTH_TOKEN_URI, data = params, verify = True)
			response = self.parse_response(request, OneDriveAPIException)
			self.set_access_token(response['access_token'])
			self.set_refresh_token(response['refresh_token'])
			return response
		except requests.exceptions.ConnectionError:
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
				request = requests.post(OneDriveAPI.OAUTH_TOKEN_URI, data = params)
				response = self.parse_response(request, OneDriveAPIException)
				self.set_access_token(response['access_token'])
				self.set_refresh_token(response['refresh_token'])
				return response
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def sign_out(self):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.OAUTH_SIGNOUT_URI + '?client_id=' + self.client_id + '&redirect_uri=' + self.client_redirect_uri)
				return self.parse_response(r, OneDriveAuthError)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def get_recent_docs(self):
		raise NotImplementedError('get_recent_docs is not implemented.')
	
	def get_quota(self, user_id = 'me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id + '/skydrive/quota')
				return self.parse_response(r, OneDriveAPIException)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def get_root_entry_name(self):
		return 'me/skydrive'
	
	def get_property(self, entry_id = 'me/skydrive'):
		try:
			r = self.http_client.get(OneDriveAPI.API_URI + entry_id)
			return self.parse_response(r, OneDriveAPIException)
		except OneDriveAuthError:
			self.auto_recover_auth_error()
			return self.get_property(entry_id)
		except requests.exceptions.ConnectionError:
			self.logger.info('network connection error.')
			self.threadman.hang_caller()
			return self.get_property(entry_id)
	
	def set_property(self, entry_id, **kwargs):
		'''
		Different types of files have different RW fields.
		Refer to http://msdn.microsoft.com/en-us/library/dn631831.aspx.
		Example:
			self.set_property(your_id, name = 'new name', description = 'new desc')
		'''
		headers = {
			'Content-Type': 'application/json',
		}
		while True:
			try:
				r = self.http_client.put(OneDriveAPI.API_URI + entry_id, data = json.dumps(kwargs), headers = headers)
				return self.parse_response(r, OneDriveAPIException)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def get_link(self, entry_id, type = 'r'):
		'''
		Return a link to share the entry.
		@param type: one of 'r' (default), 'rw', 'e' (short for 'embed').
		'''
		if type == 'r': type = 'shared_read_link'
		elif type == 'rw': type = 'shared_edit_link'
		else: type = 'embed'
		
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/' + type)
				return self.parse_response(r, OneDriveAPIException)['source']
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def list_entries(self, folder_id = 'me/skydrive', type = 'files'):
		'''
		@param type: 'files' (default) for all files. 'shared' for shared files (used internally).
		'''
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + folder_id + '/' + type)
				return self.parse_response(r, OneDriveAPIException)['data']
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def list_shared_entries(self, user_id = 'me'):	
		return self.list_entries(user_id + '/skydrive', 'shared')
	
	def mkdir(self, folder_name, parent_id = 'me/skydrive'):
		if parent_id == '/': parent_id = 'me/skydrive'	# fix parent_id alias
		data = {'name': folder_name}
		headers = {'Content-Type': 'application/json'}
		uri = OneDriveAPI.API_URI + parent_id
		while True:
			try:
				r = self.http_client.post(uri, data = json.dumps(data), headers = headers)
				return self.parse_response(r, OneDriveAPIException, requests.codes.created)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def cp(self, target_id, dest_folder_id, overwrite = True, type = 'COPY'):
		'''
		Return an entry dict if opeation succeeds.
		@param overwrite: whether or not to overwrite an existing entry. True, False, None (ChooseNewName).
		'''
		if overwrite == None: overwrite = 'ChooseNewName'
		data = {'destination': dest_folder_id}
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + self.client_access_token
		}
		uri = OneDriveAPI.API_URI + target_id + '?overwrite=' + str(overwrite)
		req = requests.Request(type, uri, data=json.dumps(data), headers=headers).prepare()
		while True:
			try:
				r = self.http_client.send(req)
				return self.parse_response(r, OneDriveAPIException, requests.codes.created)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def mv(self, target_id, dest_folder_id, overwrite = True):
		return self.cp(target_id, dest_folder_id, overwrite, 'MOVE')
	
	def put(self, name, folder_id = 'me/skydrive', upload_location = None, local_path = None, data = None, overwrite = True):
		'''
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
		
		One issue is image resizing.
		Another issue is timestamp correction.
		'''
		uri = OneDriveAPI.API_URI
		if upload_location != None: uri += upload_location # already ends with '/'
		else: uri += folder_id + '/files/'
		
		if name == '': raise OneDriveValueError({'error': 'empty_name', 'error_description': 'The file name cannot be empty.'})
		uri += name
		
		# is checking file type necessary?
		d = {
			'downsize_photo_uploads': False,
			'overwrite': overwrite
		}
		url += urllib.parse.urlencode(d)
		
		if data != None: pass
		elif local_path != None:
			if not os.path.isfile(local_path):
				raise OneDriveValueError({'error': 'wrong_file_type', 'error_description': 'The local path "' + local_path + '" is not a file.'})
			else:
				data = open(local_path, 'rb')
		else:
			raise OneDriveValueError({'error': 'upload_null_content', 'error_description': 'local_path and data cannot both be null.'})
		
		while True:
			try:
				r = self.http_client.put(uri, data = data)
				ret = r.json()
				if r.status_code != requests.codes.ok and r.status_code != requests.codes.created:
					# TODO: try testing this
					if 'error' in ret and 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired': 
						raise OneDriveAuthError(ret)
					else: raise OneDriveAPIException(ret)
				return ret
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
		
	def get(self, entry_id, local_path = None):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + entry_id + '/content')
				if r.status_code != requests.codes.ok:
					ret = r.json()
					# TODO: try testing this
					if 'error' in ret and 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired': 
						raise OneDriveAuthError(ret)
					else: raise OneDriveAPIException(ret)
				if local_path != None:
					with open(local_path, 'wb') as f: f.write(r.content)
				else: return r.content
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def rm(self, entry_id):
		'''
		OneDrive API always returns HTTP 204.
		'''
		while True:
			try:
				self.http_client.delete(OneDriveAPI.API_URI + entry_id)
				return
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def get_user_info(self, user_id = 'me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id)
				return self.parse_response(r, OneDriveAPIException, requests.codes.ok)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	
	def get_contact_list(self, user_id = 'me'):
		while True:
			try:
				r = self.http_client.get(OneDriveAPI.API_URI + user_id + '/friends')
				return self.parse_response(r, OneDriveAPIException, requests.codes.ok)
			except OneDriveAuthError:
				self.auto_recover_auth_error()
			except requests.exceptions.ConnectionError:
				self.logger.info('network connection error.')
				self.threadman.hang_caller()
	