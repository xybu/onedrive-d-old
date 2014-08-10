#!/usr/bin/python3

import config
import live_api

config.load_config()
api = live_api.OneDrive_API(config.APP_CLIENT_ID, config.APP_CLIENT_SECRET)
api.set_access_token(config.APP_CONFIG['token']['access_token'])


#print(root)

try:
	print('MKDIR RETURNS:\n')
	print(api.mkdir('test'))
except live_api.OperationError as e:
	print(e)

target = None

for entry in api.list_entries():
	if entry['name'] == 'test':
		# print(entry)
		target = entry
		break

if target != None:
	print(api.rmdir(target['id']))
else:
	print('folder test does not exist')
