#!/bin/bash

# Setup script for onedrive-d
# Usage:
# ./setup.sh [inst|remove]
# 
# @author	Xiangyu Bu <xybu92@live.com>

DISTRIB_ID=`cat /etc/lsb-release | grep 'DISTRIB_ID=' | cut -d '=' -f2`
DISTRIB_ID=${DISTRIB_ID,,}

test_cmd() {
	[ -x "$(which $1)" ]
}

case $DISTRIB_ID in
	debian|ubuntu)
		PYGOBJECT_PKG_NAME='python3-gi'
		GIT_PKG_NAME='git'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo apt-get install'
		;;
	fedora)
		PYGOBJECT_PKG_NAME='pygobject3'
		GIT_PKG_NAME='git-core'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo yum install'
		;;
	*)
		echo "This setup script does not support your distro $DISTRIB_ID."
		exit 1
		;;
esac

case $1 in
	inst)
		sudo rm -rf temp onedrive_d/temp build onedrive_d/build dist onedrive_d/dist *.egg-info onedrive_d/*.egg-info setup.cfg onedrive_d/setup.cfg onedrive_d/__pycache__
		$INSTALL_CMD $GIT_PKG_NAME $SETUPTOOL_PKG_NAME $PYGOBJECT_PKG_NAME $INOTIFY_PKG_NAME
		sudo python3 onedrive_d/setup.py install
		sudo python3 onedrive_d/setup.py clean
		sudo rm -rf temp onedrive_d/temp build onedrive_d/build dist onedrive_d/dist *.egg-info onedrive_d/*.egg-info setup.cfg onedrive_d/setup.cfg onedrive_d/__pycache__
		mkdir ~/.onedrive
		cp default/ignore_list.txt ~/.onedrive/ignore_list.txt
		echo ""
		echo "Please issue command 'onedrive-pref [--no-gui]' to configure the app,"
		echo "and then issue command 'onedrive-d [--no-gui]' to start the daemon."
		;;
	remove)
		sudo pip uninstall onedrive_d
		sudo pip3 uninstall onedrive_d
		echo ""
		echo "onedrive_d has been removed from the system."
		;;
	*)
		echo "Usage ./setup.sh [inst|remove]"
		echo "	inst: install onedrive-d"
		echo "	remove: uninstall onedrive-d from the system"
		exit 1
		;;
esac

echo "All operations finished."

exit 0
