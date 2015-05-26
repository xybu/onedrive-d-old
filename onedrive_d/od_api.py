"""
OneDrive API class and exception definitions.
	OneDriveException -- base class of all API exceptions.
	OneDriveClient -- contains client-level information.
		Can derive OneDriveAccount instances.
	OneDriveAccount -- contains account-level information. 
		Some methods rely on OneDriveClient.
		Can derive OneDriveEntDrive instances.
	OneDriveEntDrive -- abstracts Drive resource.
		Can derive OneDriveEntItem instances.
	OneDriveEntItem -- abstracts files, folders, and other resources.
	OneDriveEntOwner -- abstracts owner identity.
"""

import time
import urllib
import requests
from . import od_bootstrap
from . import od_sleepq


APP_CLIENT_ID = '000000004010C916'
APP_CLIENT_SECRET = 'PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi'
APP_REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'


class OneDriveException(Exception):

	def __init__(self, error_with_description):
		super().__init__()
		if 'error_description' in error_with_description:
			self.errno = error_with_description['error']
			self.strerror = error_with_description['error_description']
		elif 'error' in error_with_description:
			self.errno = error_with_description['error']['code']
			self.strerror = error_with_description['error']['message']
			if self.errno == 'request_token_expired':
				self.__class__ = OneDriveAuthException
		else:
			raise ValueError('Unknown OneDrive error format - ' + str(error_with_description))

	def __str__(self):
		return self.strerror + ' (' + self.errno + ')'


class OneDriveAuthException(OneDriveException):
	"""
	There are two flows to generate such type of exception:
		(1) When exchanging / renewing a token
		(2) When requesting a resource / performing an action
	The second flow is usually caught and will cause a retry.
	"""
	pass


class OneDriveAccount:
	"""
	This class abstracts information for a single OneDrive account.
	Data fields: account_id, account_type, token_type, access_token, refresh_token, token_expiration.
	There are two flows to form a valid OneDriveAccount object:
		(1) call OneDriveClient.get_account() to exchange a code to account info.
		(2) call constructor with Non-None saved_record to restore an old account.
	"""

	def __init__(self, account_type='personal', saved_record=None, client=None):
		self.account_type = account_type
		self.session = requests.Session()
		self.client = client
		if account_type == 'personal':
			self.api_url = 'https://api.onedrive.com/v1.0'
		elif account_type == 'business':
			# self.api_url = 'https://{tenant}-my.sharepoint.com/_api/v2.0'
			raise NotImplementedError('Support for OneDrive for Business has not been implemented yet.')
		if saved_record is not None:
			self.__dict__.update(saved_record)
			self.session.headers.update({'Authorization': 'Bearer ' + self.access_token})

	def set_client(self, client):
		self.client = client

	def exchange_token(self, code=None, uri=None, redirect_uri=APP_REDIRECT_URI):
		if uri is not None and '?' in uri:
			qs_dict = urllib.parse.parse_qs(uri.split('?')[1])
			if 'code' in qs_dict:
				code = qs_dict['code']
		if code is None:
			raise ValueError('Authorization code is not specified.')
		params = {
			'client_id': self.client.client_id,
			'client_secret': self.client.client_secret,
			'redirect_uri': redirect_uri,
			'code': code,
			'grant_type': 'authorization_code'
		}
		while True:
			try:
				req = requests.post('https://login.live.com/oauth20_token.srf',
					data=params, verify=True)
				if req.status_code != requests.codes.ok:
					raise OneDriveAuthException(req.json())
				self.load_token(req.json())
				return True
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def load_token(self, oauth_token_response):
		self.account_id = oauth_token_response['user_id']
		self.token_type = oauth_token_response['token_type']
		self.access_token = oauth_token_response['access_token']
		self.refresh_token = oauth_token_response['refresh_token']
		self.token_expiration = int(time.time()) + oauth_token_response['expires_in']
		self.session.headers.update({'Authorization': 'Bearer ' + self.access_token})

	def renew_token(self, redirect_uri = APP_REDIRECT_URI):
		# assume self.refresh_token has been set
		params = {
			'client_id': self.client.client_id,
			'client_secret': self.client.client_secret,
			'redirect_uri': redirect_uri,
			'refresh_token': self.refresh_token,
			'grant_type': 'refresh_token'
		}
		while True:
			try:
				req = requests.post('https://login.live.com/oauth20_token.srf',
					data=params, verify=True)
				if req.status_code != requests.codes.ok:
					raise OneDriveAuthException(req.json())
				OneDriveClient.logger.debug('Access token renewed.')
				return self.load_token(req.json())
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def get_profile(self):
		"""
		If success, return a dict with fields 'first_name', 'last_name', 'name'
		'id', 'gender', and 'locale' of the account owner.
		"""
		while True:
			try:
				req = self.session.get('https://apis.live.net/v5.0/me')
				if req.status_code != requests.codes.ok:
					raise OneDriveException(req.json())
				return req.json()
			except OneDriveAuthException:
				self.renew_token()
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def sign_out(self, redirect_uri=APP_REDIRECT_URI):
		"""
		Sign the account out. The account object is still valid until it is
		destroyed.
		"""
		params = {
			'client_id': self.client.client_id,
			'redirect_uri': redirect_uri
		}
		uri = 'https://login.live.com/oauth20_logout.srf?' + urllib.parse.urlencode(params)
		while True:
			try:
				req = self.session.get(uri)
				if req.status_code == requests.codes.ok:
					self.client.delete_account(self)
					return True
			except OneDriveAuthException:
				self.renew_token()
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def get_all_drives(self):
		uri = self.api_url + '/drives'
		while True:
			try:
				req = self.session.get(uri)
				if req.status_code != requests.codes.ok:
					raise OneDriveException(req.json())
				ret = {}
				for d in req.json()['value']:
					o = OneDriveEntDrive(self, api_json=d)
					ret[o.id] = o
				return ret
			except OneDriveAuthException:
				self.renew_token()
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def get_drive(self, drive_id=None):
		"""If drive_id is None, return the default Drive."""
		uri = self.api_url + '/drive'
		if drive_id is not None:
			uri = uri + 's/' + drive_id
		while True:
			try:
				req = self.session.get(uri)
				if req.status_code != requests.codes.ok:
					raise OneDriveException(req.json())
				return OneDriveEntDrive(self, api_json=req.json())
			except OneDriveAuthException:
				self.renew_token()
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def dump(self):
		return self.__dict__

class OneDriveClient:
	"""
	Main API driver and creator of other API data objects.
	"""
	# The singletons must be previously initialized by MainThread
	logger = od_bootstrap.get_logger()
	sleep_queue = od_sleepq.get_instance()

	def __init__(self, client_id=APP_CLIENT_ID, client_secret=APP_CLIENT_SECRET, 
		client_scope=['wl.signin', 'wl.offline_access', 'onedrive.readwrite']):
			self.client_id = client_id
			self.client_secret = client_secret
			self.client_scope = client_scope
			self.accounts = {}

	def get_oauth_url(self, display='touch', locale='en',
		redirect_uri=APP_REDIRECT_URI):
		"""Return sign-in url for code-flow authentication."""
		params = {
			'client_id' : self.client_id,
			'scope': ' '.join(self.client_scope),
			'response_type': 'code',
			'display': display,
			'locale': locale,
			'redirect_uri': redirect_uri
		}
		return 'https://login.live.com/oauth20_authorize.srf?' + urllib.parse.urlencode(params)

	def get_account(self, account_type='personal', code=None, uri=None):
		"""
		Get a new account object from auth code or auth uri, and then
		add the object to account dict.
		"""
		acct = OneDriveAccount(account_type, client=self)
		acct.exchange_token(self, code, uri)
		self.add_account(acct)
		return acct

	def add_account(self, account):
		"""
		Add a stored account obj to account dict.
		"""
		self.accounts[account.account_id] = account

	def delete_account(self, account):
		del self.accounts[account.account_id]


class OneDriveEntOwner:

	def __init__(self, json_value):
		if 'user' in json_value:
			self.owner_id = json_value['user']['id']
			self.owner_name = json_value['user']['displayName']
			self.owner_type = 'user'
		else:
			raise ValueError('Unknown owner type: ' + str(json_value))

	def dump(self):
		return self.__dict__

	def __str__(self):
		return "Owner Resource({0}, {1}, {2})".format(self.owner_type, self.owner_id, self.owner_name)


class OneDriveEntDrive:

	def __init__(self, account=None, api_json=None, saved_record=None):
		self.account = account
		if api_json is not None:
			self.local_root = None
			self.load_from_api_response(api_json)
		elif saved_record is not None:
			self.load_from_saved_record(saved_record)

	def load_from_api_response(self, api_json):
		self.id = api_json['id']
		self.drive_type = api_json['driveType']
		self.owner = OneDriveEntOwner(api_json['owner'])
		self.quota_total = api_json['quota']['total']
		self.quota_used = api_json['quota']['used']
		self.quota_remaining = api_json['quota']['remaining']
		self.quota_deleted = api_json['quota']['deleted']
		self.quota_state = api_json['quota']['state']
		# for a new Drive, one needs to set a corresponding local_path later

	def load_from_saved_record(self, saved_record):
		self.owner = OneDriveEntOwner({
			saved_record['owner_type']: {
				'id': saved_record['owner_id'],
				'displayName': saved_record['owner_name']
			}
		})
		del saved_record['owner_type']
		del saved_record['owner_name']
		del saved_record['owner_id']
		self.__dict__.update(saved_record)

	def set_account(self, account):
		self.account = account

	def set_local_root(self, path):
		self.local_root = path

	def get_root(self, expand='', children_only=False):
		pass

	def get_changes(self):
		pass

	def find_item(self, q):
		pass

	def dump(self):
		return self.__dict__

	def __str__(self):
		return 'Drive(' + str(self.__dict__) + ')'

class OneDriveEntItem:
	pass
