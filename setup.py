#!/usr/bin/env python

import os
from setuptools import setup, find_packages

pkg_root = os.path.dirname(__file__)

try:
	readme = open(os.path.join(pkg_root, 'README.md')).read()
except IOError:
	readme = 'Please read README.md for more details'

setup(
	name='onedrive-d',
	version='0.7',
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
	
	install_requires = ['PyYAML', 'requests', 'urllib3', 'python-skydrive'],
	
	packages=find_packages(),
	# include_package_data=True,
	scripts=['onedrive/onedrive-daemon','onedrive/onedrive-utils'],
	exclude_package_data={'': ['README.*']}

	#entry_points=dict(console_scripts=[
	#	'onedrive-d = onedrive/onedrive-daemon'])
)

