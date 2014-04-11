#!/usr/bin/env python

import os
from setuptools import setup, find_packages

try:
	readme = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
except IOError:
	readme = 'Please read README.md for more details'

setup(
	name='onedrive-d',
	version='0.7.1',
	author='Xiangyu Bu',
	author_email='xybu92@live.com',
	license='MIT',
	keywords=[ 'skydrive', 'onedrive', 'microsoft', 'daemon', 'live', 'liveconnect',
		'cloud', 'storage', 'storage provider', 'file hosting' ],

	url='http://github.com/xybu92/onedrive-d',
	
	description='A Microsoft OneDrive client that works for Ubuntu-based Linux',
	
	long_description=readme,
	
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'Intended Audience :: Information Technology',
		'License :: OSI Approved',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 2 :: Only',
		'Topic :: Internet',
		'Topic :: Software Development',
		'Topic :: System :: Archiving',
		'Topic :: System :: Filesystems',
		'Topic :: Utilities'],
	
	install_requires = ['PyYAML', 'requests', 'urllib3', 'python-onedrive'],
	
	packages=find_packages(),
	include_package_data=True,
	package_data={'onedrive_d': ['res/*.png']},
	#scripts=['daemon/onedrive-daemon','daemon/onedrive-utils'],
	exclude_package_data={'': ['README.*']},

	entry_points = dict(console_scripts=[
		'onedrive-d = onedrive_d.daemon:main', 
		'onedrive-auth = onedrive_d.auth:main', 
		'onedrive-util = onedrive_d.util:main'])
)

