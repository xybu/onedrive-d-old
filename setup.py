#!/usr/bin/env python

from setuptools import setup, find_packages
import os

pkg_root = os.path.dirname(__file__)

# Error-handling here is to allow package to be built w/o README included
try:
	readme = open(os.path.join(pkg_root, 'README.md')).read()
except IOError:
	readme = ''

setup(

	name='onedrive-d',
	version='0.6',
	author='Xiangyu Bu',
	author_email='xybu92@live.com',
	license='MIT',
	keywords=[ 'skydrive', 'onedrive', 'microsoft', 'daemon', 'live', 'liveconnect',
		'cloud', 'storage', 'storage provider', 'file hosting' ],

	url='http://github.com/xybu92/onedrive-d',

	description='A Microsoft OneDrive daemon written in Python',
	
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
	#extras_require=dict(
	#	standalone=['PyYAML', 'requests', 'urllib3', 'python-skydrive'],
	#	cli=['PyYAML', 'requests', 'urllib3', 'python-skydrive'],
	#	conf=['PyYAML', 'requests', 'urllib3', 'python-skydrive']),

	packages=['onedrive'],
	scripts=['onedrive/onedrive-daemon','onedrive/onedrive-utils'],
	include_package_data=True,
	#package_data={'': ['README.md']},
	exclude_package_data={'': ['README.*']}

	#entry_points=dict(console_scripts=[
	#	'onedrive-d = onedrive/onedrive.py'])
	)

