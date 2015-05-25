"""
OneDrive API class and exception definitions.
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
		self.errno = error_with_description['error']
		self.strerror = error_with_description['error_description']

	def __str__(self):
		return self.strerror + ' (' + self.errno + ')'


class OneDriveAuthException(OneDriveException):
	pass


class OneDriveAccount:
	"""
	This class abstracts information for a single OneDrive account.
	Data fields: account_id, account_type, token_type, access_token, refresh_token, token_expiration.
	There are two flows to form a valid OneDriveAccount object:
		(1) call OneDriveClient.get_account() to exchange a code to account info.
		(2) call constructor with Non-None saved_record to restore an old account.
	"""

	def __init__(self, account_type='personal', saved_record=None):
		self.account_type = account_type
		self.session = requests.Session()
		if saved_record is not None:
			self.__dict__.update(saved_record)
			self.session.headers.update({'Authorization': 'Bearer ' + self.access_token})

	def exchange_token(self, client, code=None, uri=None, redirect_uri=APP_REDIRECT_URI):
		if uri is not None and '?' in uri:
			qs_dict = urllib.parse.parse_qs(uri.split('?')[1])
			if 'code' in qs_dict:
				code = qs_dict['code']
		if code is None:
			raise ValueError('Authorization code is not specified.')
		params = {
			'client_id': client.client_id,
			'client_secret': client.client_secret,
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

	def renew_token(self, client, redirect_uri = APP_REDIRECT_URI):
		# assume self.refresh_token has been set
		params = {
			'client_id': client.client_id,
			'client_secret': client.client_secret,
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
			except requests.exceptions.ConnectionError as e:
				OneDriveClient.logger.warning('Connection error - %s' % e)
				OneDriveClient.sleep_queue.hang_caller()

	def sign_out(self, client, redirect_uri=APP_REDIRECT_URI):
		"""
		Sign the account out. The account object is still valid until it is
		destroyed.
		"""
		params = {
			'client_id': client.client_id,
			'redirect_uri': redirect_uri
		}
		uri = 'https://login.live.com/oauth20_logout.srf?' + urllib.parse.urlencode(params)
		while True:
			try:
				req = self.session.get(uri)
				if req.status_code == requests.codes.ok:
					client.delete_account(self)
					return True
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
		acct = OneDriveAccount(account_type)
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
