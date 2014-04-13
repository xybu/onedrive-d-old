#!/usr/bin/python

import xattr

x = xattr.xattr('test_file_dup')

print x

print x.keys()

print dict(x)

### add properties

x['onedrive_id'] = "12345"
x['onedrive_id_dup'] = "12345666"

print dict(x)

del x['onedrive_id_dup']

print (x)

