#!/usr/bin/python3

'''
OneDrive REST API implemented in Python 3.

The goal is to make the API as lightweight as possible.
API Document: http://msdn.microsoft.com/en-us/library/dn659752.aspx

@author	Xiangyu Bu <xybu92@live.com>
'''

import json
import requests
import os
from urllib import parse

class OneDrive_Error(Exception):
	def __init__(self, args):
		if 'error_description' in args:
			self.errno = args['error']
			self.message = args['error'] + ': ' + args['error_description']
		elif 'error' in args:
			self.errno = args['error']['code']
			self.message = args['error']['code'] + ': ' + args['error']['message']
		else:
			self.errno = 'unknown'
			self.message = json.dumps(args)
	
	def __str__(self, ex = None):
		return repr(self.message)

class AuthError(OneDrive_Error): pass
class NetworkError(OneDrive_Error):
	def __init__(self, ex):
		self.message = ex.__str__()
		self.errno = ex.errno
class ProtocolError(OneDrive_Error): pass
class OperationError(OneDrive_Error): pass

class OneDrive_API:
	DEFAULT_CLIENT_SCOPE = ['wl.skydrive', 'wl.skydrive_update', 'wl.offline_access']
	DEFAULT_REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'
	OAUTH_AUTHORIZE_URI = 'https://login.live.com/oauth20_authorize.srf'
	OAUTH_TOKEN_URI = 'https://login.live.com/oauth20_token.srf'
	OAUTH_SIGNOUT_URI = 'https://login.live.com/oauth20_logout.srf'
	API_URI = 'https://apis.live.net/v5.0/'
	FOLDER_TYPES = ['folder', 'album']
	
	def __init__(self, client_id, client_secret, client_scope = DEFAULT_CLIENT_SCOPE, redirect_uri = DEFAULT_REDIRECT_URI):
		'''
		Initialize the OneDrive API object.
		ConnectionPool uses SSL.
		'''
		self.access_token = None
		self.client_id = client_id
		self.client_secret = client_secret
		self.client_scope = client_scope
		self.client_redirect_uri = redirect_uri
		self.http_client = requests.Session()
	
	def parse_response(self, request, error, ok_status = requests.codes.ok):
		ret = request.json()
		if request.status_code != ok_status:
			if 'code' in ret['error'] and ret['error']['code'] == 'request_token_expired':
				raise AuthError(ret)
			else:
				raise error(ret)
		return ret
	
	def get_auth_uri(self, display = 'touch', locale = 'en', state = ''):
		'''
		Use the code returned in the final redirect URL to exchange for
		an access token
		
		http://msdn.microsoft.com/en-us/library/dn659750.aspx
		'''
		uri = OneDrive_API.OAUTH_AUTHORIZE_URI + "?client_id=" + self.client_id + "&scope=" + '%20'.join(self.client_scope) + "&response_type=code&redirect_uri=" + self.client_redirect_uri + "&display=" + display
		if locale != "en":
			uri = uri + "&locale=" + locale
		# TODO: state may need to be URL-encoded
		if state != "":
			uri = uri + "&state=" + state
		return uri
	
	def is_ready(self):
		return self.access_token != None
	
	def set_access_token(self, token):
		self.access_token = token
		self.http_client.headers.update({'Authorization': 'Bearer ' + self.access_token})
	
	def get_access_token(self, code = None, uri = None):
		'''
		http://msdn.microsoft.com/en-us/library/dn659750.aspx
		
		return a dict with keys token_type, expires_in, scope, 
		access_token, refresh_token, authentication_token
		'''
		if uri != None and '?' in uri:
			qs_dict = parse.parse_qs(uri.split('?')[1])
			if 'code' in qs_dict:
				code = qs_dict['code']
		if code == None:
			raise ProtocolError('access_code_not_found', 'The access code is not specified.')
		
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"code": code,
			"grant_type": "authorization_code"
		}
		try:
			r = requests.post(OneDrive_API.OAUTH_TOKEN_URI, data = params, verify = True)
			return self.parse_response(r, AuthError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def sign_out(self):
		r = self.http_client.get(OAUTH_SIGNOUT_URI + '?client_id=' + self.client_id + '&redirect_uri=' + self.client_redirect_uri)
		return self.parse_response(r, AuthError)
	
	def refresh_token(self, refresh_token):
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"refresh_token": refresh_token,
			"grant_type": 'refresh_token'
		}
		try:
			r = requests.post(OneDrive_API.OAUTH_TOKEN_URI, data = params)
			return self.parse_response(r, AuthError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_recent_docs(self, user_id = 'me'):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + user_id + '/skydrive/recent_docs')
			return self.parse_response(r, ProtocolError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_quota(self, user_id = 'me'):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + user_id + '/skydrive/quota')
			return self.parse_response(r, ProtocolError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_root_entry_name(self):
		return 'me/skydrive'
	
	def get_property(self, entry_id = 'me/skydrive'):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + entry_id)
			return self.parse_response(r, ProtocolError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
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
		try:
			r = self.http_client.put(OneDrive_API.API_URI + entry_id, data = json.dumps(kwargs), headers = headers)
			return self.parse_response(r, ProtocolError)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_link(self, entry_id, type = 'r'):
		'''
		Return a link to share the entry.
		@param type: one of 'r' (default), 'rw', 'e' (short for 'embed').
		'''
		if type == 'r': type = 'shared_read_link'
		elif type == 'rw': type = 'shared_edit_link'
		else: type = 'embed'
		try:
			r = self.http_client.get(OneDrive_API.API_URI + entry_id + '/' + type)
			return self.parse_response(r, ProtocolError)['source']
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def list_entries(self, folder_id = 'me/skydrive', type = 'files'):
		'''
		@param type: 'files' (default) for all files. 'shared' for shared files (used internally).
		'''
		try:
			r = self.http_client.get(OneDrive_API.API_URI + folder_id + '/' + type)
			return self.parse_response(r, ProtocolError)['data']
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def list_shared_entries(self, user_id = 'me'):	
		return self.list_entries(user_id + '/skydrive', 'shared')
	
	def mkdir(self, folder_name, parent_id = 'me/skydrive'):
		if parent_id == '/': parent_id = 'me/skydrive'	# fix parent_id alias
		data = {'name': folder_name}
		headers = {
			'Content-Type': 'application/json',
		}
		uri = OneDrive_API.API_URI + parent_id
		try:
			r = self.http_client.post(uri, data = json.dumps(data), headers = headers)
			return self.parse_response(r, OperationError, requests.codes.created)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def cp(self, target_id, dest_folder_id, overwrite = True, type = 'COPY'):
		'''
		Return an entry dict if opeation succeeds.
		@param overwrite: whether or not to overwrite an existing entry. True, False, None (ChooseNewName).
		'''
		if overwrite == None: overwrite = 'ChooseNewName'
		data = {'destination': dest_folder_id}
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + self.access_token
		}
		uri = OneDrive_API.API_URI + target_id + '?overwrite=' + str(overwrite)
		req = requests.Request(type, uri, data=json.dumps(data), headers=headers).prepare()
		try:
			r = self.http_client.send(req)
			return self.parse_response(r, OperationError, requests.codes.created)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
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
		
		@raises live_api.OperationError
		@raises live_api.ProtocolError
		@raises OSError
		@raises live_api.NetworkError
		
		To put an empty file, either local_path points to an empty file or data is set ''.
		To upload a dir, check if it exists, and then send recursive puts to upload its files.
		'''
		uri = OneDrive_API.API_URI
		if upload_location != None: uri += upload_location # already ends with '/'
		else: uri += folder_id + '/files/'
		
		if name == '': raise OperationError({'error': 'empty_name', 'error_description': 'The file name cannot be empty.'})
		uri += name
		
		if overwrite == True: uri += '?overwrite=true'
		
		if data != None: pass
		elif local_path != None:
			if not os.path.isfile(local_path):
				raise OperationError({'error': 'wrong_file_type', 'error_description': 'The local path "' + local_path + '" is not a file.'})
			else:
				data = open(local_path, 'rb')
		else:
			raise OperationError({'error': 'upload_null_content', 'error_description': 'local_path and data cannot both be null.'})
		
		try:
			r = self.http_client.put(uri, data = data)
			ret = r.json()
			if r.status_code != requests.codes.ok and r.status_code != requests.codes.created:
				if 'request_token_expired' in ret: raise AuthError(ret)
				else: raise ProtocolError(ret)
			return ret
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
		
	def get(self, entry_id, local_path = None):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + entry_id + '/content')
			if r.status_code != requests.codes.ok:
				if 'request_token_expired' in ret: raise AuthError(request.json())
				else: raise ProtocolError(request.json())
			if local_path != None:
				with open(local_path, 'wb') as f:
					f.write(r.content)
			else: return r.content
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def rm(self, entry_id):
		'''
		OneDrive API always returns HTTP 204.
		'''
		try:
			self.http_client.delete(OneDrive_API.API_URI + entry_id)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_user_info(self, user_id = 'me'):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + user_id)
			return self.parse_response(r, ProtocolError, requests.codes.ok)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_contact_list(self, user_id = 'me'):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + user_id + '/friends')
			return self.parse_response(r, ProtocolError, requests.codes.ok)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_current_permissions(self):
		try:
			r = self.http_client.get(OneDrive_API.API_URI + user_id + '/permissions')
			return self.parse_response(r, ProtocolError, requests.codes.ok)
		except requests.exceptions.ConnectionError as e:
			raise NetworkError(e)
	
	def get_item_preview(self, type, link):
		raise NotImplementedError('get_item_preview is not implemented')