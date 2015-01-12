#!/usr/bin/python3

import os
from setuptools import setup, find_packages

try:
	readme = open(os.path.join(os.path.dirname(__file__), '/../README.md')).read()
except IOError:
	readme = 'Please read README.md for more details'

setup(
	name='onedrive-d',
	version='1.0-dev',
	author='Xiangyu Bu',
	author_email='xybu92@live.com',
	license='GPLv3',
	keywords=['onedrive', 'microsoft', 'daemon', 'live', 'liveconnect',
		'cloud', 'storage', 'storage provider', 'file hosting', 'skydrive'],
	url='http://github.com/xybu/onedrive-d',
	description='A Microsoft OneDrive client for Debian/Ubuntu desktop.',
	long_description=readme,
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Environment :: X11 Applications',
		'Environment :: X11 Applications :: GTK',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'Intended Audience :: Information Technology',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Topic :: Internet',
		'Topic :: Software Development',
		'Topic :: System :: Archiving',
		'Topic :: System :: Filesystems',
		'Topic :: Utilities'],
	
	install_requires = ['requests', 'urllib3', 'certifi', 'send2trash'],
	
	packages=find_packages(),
	include_package_data=True,
	package_data={'onedrive_d': ['res/*.png']},
	#scripts=['daemon/onedrive-daemon','daemon/onedrive-utils'],
	exclude_package_data={'': ['README.*']},

	# entry_points = dict(console_scripts=[
	#	'onedrive-d = onedrive_d.daemon:main', 
	#	'onedrive-prefs = onedrive_d.prefs:main'])
)
