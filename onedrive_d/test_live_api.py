#!/usr/bin/python3

import config
import live_api

api = live_api.OneDrive_API(config.APP_CLIENT_ID, config.APP_CLIENT_SECRET)
api.set_access_token(config.APP_CONFIG['token']['access_token'])


target = None

#for entry in api.list_entries():
#	if entry['name'] == 'Document1.docx':
#		# print(entry)
#		target = entry
#		break

#assert target != None

#print(api.set_property(target['id'], name = 'TestDoc.docx', description = 'Test change ds'))

#print(api.put('test.wav', local_path = '/home/xb/OneDrive/arribba.wav'))

#data = api.put('中文.txt', local_path = '中文.txt')
#print(data)

#with open('中文2.txt', 'wb') as f:
#	f.write(api.get(data['id']))

print(api.get_user_info())
