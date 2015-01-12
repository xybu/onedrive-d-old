#!/bin/bash

# onedrive-d setup script.
# usage: 
# ./setup.sh [inst|remove]

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
	echo "Could not determine your OS. Abort."
	exit 1
fi

DISTRIB_ID=${DISTRIB_ID,,}

case $DISTRIB_ID in
	debian|ubuntu|linuxmint|"elementary os")
		PYGOBJECT_PKG_NAME='python3-gi'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo apt-get install'
		;;
	fedora)
		PYGOBJECT_PKG_NAME='pygobject3'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo yum install'
		;;
	arch|archarm)
		PYGOBJECT_PKG_NAME='python-gobject'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python-pip'
		INSTALL_CMD='sudo pacman -S --needed'
		;;
	opensuse)
		PYGOBJECT_PKG_NAME='python-gobject'
		INOTIFY_PKG_NAME='inotify-tools'
		SETUPTOOL_PKG_NAME='python3-pip'
		INSTALL_CMD='sudo zypper install'
		;;
	*)
		echo "Setup script does not support your distro $DISTRIB_ID."
		exit 1
		;;
esac

test_cmd() {
	[ -x "$(which $1)" ]
}

print_usage() {
	echo "Usage ./setup.sh [inst|remove]"
	echo " inst: install onedrive-d"
	echo " remove: uninstall onedrive-d from the system"
	exit 0
}

if [ "$#" -ne 1 ] ; then
    print_usage
fi

case $1 in
	inst)
		$INSTALL_CMD $SETUPTOOL_PKG_NAME $PYGOBJECT_PKG_NAME $INOTIFY_PKG_NAME
		sudo ./onedrive_d/setup.py install
		sudo ./onedrive_d/setup.py clean
		mkdir ~/.onedrive
		cp onedrive_d/res/default_ignore.ini ~/.onedrive/ignore_v2.ini
		;;
	remove)
		echo "Uninstalling current version of onedrive-d..."
		sudo pip3 uninstall onedrive_d
		rm -rfv ~/.onedrive
		echo "onedrive-d has been removed from your system."
		exit 0
		;;
	*)
		usage
		;;
esac
