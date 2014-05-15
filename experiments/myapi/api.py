#!/usr/bin/python

import urllib3
import json

class OneDrive_Auth():
	client_id = None
	client_secret = None
	client_redirect_url = None
	
	auth_token_type = None
	auth_access_expiration = None
	auth_code = None
	auth_refresh_token = None
	auth_access_token = None
	
	AUTH_SCOPE = ("wl.skydrive", "wl.skydrive_update", "wl.offline_access")
	AUTH_URL = "https://login.live.com/oauth20_authorize.srf"
	AUTH_TOKEN_URL = "https://login.live.com/oauth20_token.srf"
	AUTH_DEFAULT_REDIRECT_URL = "https://login.live.com/oauth20_desktop.srf"
	
	def __init__(self, client_id, client_secret, client_redirect_url = None)
		self.client_id = client_id
		self.client_secret = client_secret
		if client_redirect_url != None:
			self.client_redirect_url = client_redirect_url
	
	def get_access_token(self):
		return self.auth_access_token
	
	def get_refresh_token(self):
		return self.auth_refreh_token
	
	def get auth_code(self):
		return self.auth_code
	
	def get_access_expiration(self):
		return self.auth_access_expiration
	
	def process_token_responseText(self, responseText = None):
		try:
			obj = json.loads(responseText)
			self.auth_token_type = obj["token_type"]
			self.auth_access_expiration = 
"""
		{
    "token_type":"bearer",   
    "expires_in":3600,
    "scope":"wl.offline_access wl.signin wl.basic",
    "access_token":"EwCo...//access token string shortened for example//...AA==",
    "refresh_token":"*LA9...//refresh token string shorted for example//...k%65",
    "authentication_token":"eyJh...//authentication token string shortened for example//...93G4"
}
"""
	
class OneDrive_API():
	
	def __init__(self, client_id, client_secret):
		pass
	
	def get_access_code_url(self):
		pass
	
	def get_
