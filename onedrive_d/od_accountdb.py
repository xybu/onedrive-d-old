"""
User account and entry database abstraction.
"""

import sqlite3
import threading


ACCOUNT_INVENTORY = '/etc/onedrived'


def get_accountdb_path(uid):
	return ACCOUNT_INVENTORY + '/' + str(uid) + '.db'


def build_empty_accountdb(uid):
	conn = sqlite3.connect(get_accountdb_path(uid), isolation_level=None)
	conn.execute("""
			CREATE TABLE IF NOT EXISTS accounts(
				account_id TEXT UNIQUE PRIMARY KEY, 
				account_token_type TEXT, 
				token_expiration_time INT, 
				access_token TEXT, 
				refresh_token TEXT
			)
		""")
	conn.execute("""
			CREATE TABLE IF NOT EXISTS drives(
				drive_id TEXT UNIQUE PRIMARY KEY,
				drive_owner_id TEXT,
				drive_owner_type TEXT,
				drive_quota_total INT,
				drive_quota_used INT,
				drive_quota_free INT,
				drive_state TEXT,
				drive_local_root TEXT
			)
		""")
	conn.execute("""
			CREATE TABLE IF NOT EXISTS entries(
				entry_id TEXT UNIQUE PRIMARY KEY,
				entry_name TEXT PRIMARY_KEY,
				parent_drive_id TEXT,
				parent_drive_path TEXT,
				parent_entry_id TEXT,
				parent_local_path TEXT,
				entry_size INT,
				create_time TEXT,
				modify_time TEXT,
				ctag TEXT,
				etag TEXT,
				entry_local_status TEXT
			)
		""")
	conn.close()


class AccountDatabaseManager:

	def __init__(self, uid):
		self.conn = sqlite3.connect(ACCOUNT_INVENTORY + '/' + str(uid) + '.db', isolation_level=None)
