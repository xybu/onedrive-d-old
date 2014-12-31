#!/bin/bash

# Setup script for onedrive-d
# Usage:
# ./setup.sh [inst|remove]
#
# @author	Xiangyu Bu <xybu92@live.com>

set -e
set -u

# Workaround to support more distros
LSB_RELEASE_BIN=$(whereis lsb-release | cut -d' ' -f2)
OS_RELEASE_BIN=$(whereis os-release | cut -d' ' -f2)

if [ -f "$LSB_RELEASE_BIN" ] ; then
	DISTRIB_ID=$(grep 'DISTRIB_ID=' $LSB_RELEASE_BIN | cut -d'=' -f2)
elif [ -f "$OS_RELEASE_BIN" ] ; then
	DISTRIB_ID=$(grep '^ID=' $OS_RELEASE_BIN | cut -d'=' -f2)
else
	echo "Could not determine your OS, aborting..."
	exit 1
fi

DISTRIB_ID=${DISTRIB_ID,,}

test_cmd() {
	[ -x "$(which $1)" ]
}

do_clean() {
	sudo rm -rf temp onedrive_d/temp build onedrive_d/build dist onedrive_d/dist *.egg-info onedrive_d/*.egg-info setup.cfg onedrive_d/setup.cfg onedrive_d/__pycache__
}

usage() {
	echo "Usage ./setup.sh [inst|remove]"
	echo "	inst: install onedrive-d"
	echo "	remove: uninstall onedrive-d from the system"
	exit 1
}

case $DISTRIB_ID in
	# Debian/Ubuntu family
	debian|ubuntu|linuxmint|"elementary os")
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
	arch|archarm)
		PYGOBJECT_PKG_NAME='python-gobject'
		GIT_PKG_NAME='git'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python-pip'
		INSTALL_CMD='sudo pacman -S --needed'
		;;
	opensuse)
		PYGOBJECT_PKG_NAME='python-gobject'
		GIT_PKG_NAME='git'
		INOTIFY_PKG_NAME='python3-pyinotify'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo zypper install'
		;;
	*)
		echo "This setup script does not support your distro $DISTRIB_ID."
		exit 1
		;;
esac

if [ "$#" -ne 1 ] ; then
    usage
fi

case $1 in
	inst)
		do_clean
		$INSTALL_CMD $GIT_PKG_NAME $SETUPTOOL_PKG_NAME $PYGOBJECT_PKG_NAME $INOTIFY_PKG_NAME
		# Add X attrib just in case
		chmod +x onedrive_d/main.py
		chmod +x onedrive_d/pref.py
		sudo python3 onedrive_d/setup.py install
		sudo python3 onedrive_d/setup.py clean
		do_clean
		mkdir ~/.onedrive
		cp default/ignore_list.txt ~/.onedrive/ignore_list.txt
		echo ""
		echo "Please issue command 'onedrive-pref [--no-gui]' to configure the app,"
		echo "and then issue command 'onedrive-d' to start the daemon."
		;;
	remove)
		echo "Removing Python 2 version of onedrive_d, if any."
		sudo pip uninstall onedrive_d
		echo "Removing Python 3 version of onedrive_d."
		sudo pip3 uninstall onedrive_d
		echo ""
		echo "onedrive_d has been removed from the system."
		;;
	*)
		usage
		;;
esac

echo "All operations finished."

exit 0
