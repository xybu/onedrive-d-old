#!/usr/bin/python

"""
Convert an OneDrive timestamp to Unix time integer.
"""

time_str_1 = "2014-03-06T18:39:34+0000"
# time_str_2 = "2014-03-06T19:39:34+0100"

import time


print time_str_1

x = time.strptime(time_str_1, '%Y-%m-%dT%H:%M:%S+0000') # to struct_time

import os

# change tz and mktime will give LOCAL time
#os.environ['TZ'] = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
#time.tzset()
# which is good because mtime is a localtime

print int(time.mktime(x))	#
print time.strftime('%Y-%m-%dT%H:%M:%S+0000', x)

print "current_epoch = " + str(int(time.time()))
