#!/usr/bin/python3

'''
OneDrive REST API implemented in Python 3.

The goal is to make the API as lightweight as possible.
API Document: http://msdn.microsoft.com/en-us/library/dn659752.aspx

@author	Xiangyu Bu <xybu92@live.com>
'''

import json
import requests
from urllib import parse

class OneDrive_Error(Exception):
	def __init__(self, args):
		self.message = args["error"] + ": " + args["error_description"]
	
	def __str__(self):
		return repr(self.message)

class NetworkError(OneDrive_Error): pass
class AuthError(OneDrive_Error): pass
class ProtocolError(OneDrive_Error): pass

class OneDrive_API:
	DEFAULT_CLIENT_SCOPE = ['wl.skydrive', 'wl.skydrive_update', 'wl.offline_access']
	DEFAULT_REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'
	OAUTH_AUTHORIZE_URI = 'https://login.live.com/oauth20_authorize.srf'
	OAUTH_TOKEN_URI = 'https://login.live.com/oauth20_token.srf'
	OAUTH_SIGNOUT_URI = 'https://login.live.com/oauth20_logout.srf'
	
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
	
	def parse_response(self, request, error_class):
		ret = request.json()
		if request.status_code != requests.codes.ok:
			raise error_class(ret)
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
		r = requests.post(OneDrive_API.OAUTH_TOKEN_URI, data = params, verify = True)
		return self.parse_response(r, AuthError)
	
	def sign_out(self):
		r = self.http_client.request('GET', OAUTH_SIGNOUT_URI + '?client_id=' + self.client_id + '&redirect_uri=' + self.client_redirect_uri)
		return self.parse_response(r, AuthError)
	
	def refresh_token(self, refresh_token):
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"redirect_uri": self.client_redirect_uri,
			"refresh_token": refresh_token,
			"grant_type": 'refresh_token'
		}
		r = requests.post(OneDrive_API.OAUTH_TOKEN_URI, data = params)
		return self.parse_response(r, AuthError)
	
	