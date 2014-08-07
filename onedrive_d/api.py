#!/usr/bin/python3

"""
A light-weight Live Connect OneDrive-RESTful API

The goal is to make the implementation as lightweight as possible
and leave the higher layer as much freedom as possible

Refer to http://msdn.microsoft.com/en-us/library/dn659752.aspx

@author	Xiangyu Bu <xybu92@live.com>
"""

import urllib3
import json
import config

class OneDriveException(Exception):
	pass

class InvalidStateError(OneDriveException):
	def __init__(self, msg):
		self.message = msg
	
	def __str__(self):
		return repr(self.message)

class AuthorizationError(OneDriveException):
	def __init__(self, args):
		self.message = args["error"] + ": " + args["error_description"]
	
	def __str__(self):
		return repr(self.message)

class OneDrive_API:
	CLIENT_ID = None
	CLIENT_SECRET = None
	CLIENT_REDIRECT_URI = None
	CLIENT_SCOPE = ['wl.skydrive', 'wl.skydrive_update', 'wl.offline_access']
	
	OAUTH_AUTHORIZE_URI = "https://login.live.com/oauth20_authorize.srf"
	OAUTH_TOKEN_URI = "https://login.live.com/oauth20_token.srf"
	OAUTH_SIGNOUT_URI = "https://login.live.com/oauth20_logout.srf"
	
	httpClient = None
	accessTokenData= None
	
	def __init__(self, client_id, client_secret, scope = None, redirect_uri = "https://login.live.com/oauth20_desktop.srf"):
		"""
		Initialize the OneDrive API object. Parameters:
			* client_id (required)
			* client_secret (required)
			* scope (optional): if unset, default value (wl.skydrive, wl.offline_access, wl.skydrive_update) will be used
			* redirect_uri (optional): if unset, default value will be used
		"""
		
		if scope != None:
			self.CLIENT_SCOPE = scope
		
		self.CLIENT_ID = client_id
		self.CLIENT_SECRET = client_secret
		self.CLIENT_REDIRECT_URI = redirect_uri
		
		assert self.CLIENT_ID != None, "Client id must not be None"
		assert self.CLIENT_SECRET != None, "Client secret must not be None"
		assert self.CLIENT_REDIRECT_URI != None, "Redirect Uri must be set"
		
		self.httpClient = urllib3.PoolManager()
	
	def get_auth_uri(self, display = "touch", locale = "en", state = ""):
		"""http://msdn.microsoft.com/en-us/library/dn659750.aspx
		Use the code returned in the final redirect URL to exchange for
		an access token
		"""
		uri = OneDrive_API.OAUTH_AUTHORIZE_URI + "?client_id=" + self.CLIENT_ID + "&scope=" + '%20'.join(self.CLIENT_SCOPE) + "&response_type=code&redirect_uri=" + self.CLIENT_REDIRECT_URI + "&display=" + display
		if locale != "en":
			uri = uri + "&locale=" + locale
		#//TODO: state may need to be URL-encoded
		if state != "":
			uri = uri + "&state=" + state
		return uri
	
	def get_access_token(self, code):
		"""http://msdn.microsoft.com/en-us/library/dn659750.aspx"""
		params = {
			"client_id": self.CLIENT_ID,
			"client_secret": self.CLIENT_SECRET,
			"redirect_uri": self.CLIENT_REDIRECT_URI,
			"code": code,
			"grant_type": "authorization_code"
		}
		r = self.httpClient.request("POST", OneDrive_API.OAUTH_TOKEN_URI, fields = params, encode_multipart = False)
		data = json.loads(r.data)
		if r.status != 200:
			raise AuthorizationError(data)
		return data
	
	def load_saved_token(self, token_json_obj, start_time = None):
		"""http://msdn.microsoft.com/en-us/library/dn659750.aspx
		token_json_obj (required): the json object previously returned by get_access_token method
		start_time (optional): the time when token expiration starts
		"""
		keys = ["access_token", "token_type", "expires_in", "scope", "authentication_token", "refresh_token"]
		token_obj = {}
		for k in keys:
			if k in token_json_obj:
				token_obj[k] = token_json_obj[k]
		
		self.accessTokenData = token_obj		
	
	def get_refresh_token(self, token_json_obj = None):
		"""http://msdn.microsoft.com/en-us/library/dn659750.aspx
		raises:
			InvalidStateError if no access token is loaded
			AuthorizationError if OneDrive returns any error
		"""
		if token_json_obj != None:
			self.load_saved_token(token_json_obj)
		
		if self.accessTokenData == None:
			raise InvalidStateError("OneDrive API has not loaded any previously saved access token to refresh.")
		
		params = {
			"client_id": self.CLIENT_ID,
			"client_secret": self.CLIENT_SECRET,
			"redirect_uri": self.CLIENT_REDIRECT_URI,
			"refresh_token": self.accessTokenData["refresh_token"],
			"grant_type": "refresh_token"
		}
		
		r = self.httpClient.request("POST", OneDrive_API.OAUTH_TOKEN_URI, fields = params, encode_multipart = False)
		data = json.loads(r.data)
		if r.status != 200:
			raise AuthorizationError(data)
		return data
	
	def get_sign_out_uri(self):
		return OneDrive_API.OAUTH_SIGNOUT_URI + "?client_id=" + self.CLIENT_ID +  "&redirect_uri=" + self.CLIENT_REDIRECT_URI
	
# test driver
def main():
	api = OneDrive_API(client_id = config.APP_CREDENTIALS["client_id"], client_secret = config.APP_CREDENTIALS["client_secret"])
	print(api.get_auth_uri())
	print(api.get_access_token("99314d29-c845-4854-5c09-f3dd6ccf604e"))

if __name__ == "__main__":
	main()
