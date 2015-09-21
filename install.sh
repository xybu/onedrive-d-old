#!/bin/bash

# For debugging, exit immediately if a command fails
set -e
# For debugging, treat unset variables as errors if used 
set -u

do_clean() {
	sudo rm -rf temp onedrive_d/temp build onedrive_d/build dist onedrive_d/dist *.egg-info \
	    onedrive_d/*.egg-info setup.cfg onedrive_d/setup.cfg onedrive_d/__pycache__
}

CURRENT_USER=$(whoami)

# Workaround to support more distros
LSB_RELEASE_BIN=$(whereis lsb-release | cut -d' ' -f2)
OS_RELEASE_BIN=$(whereis os-release | cut -d' ' -f2)

if [ -f "$LSB_RELEASE_BIN" ] ; then
	DISTRIB_ID=$(grep 'DISTRIB_ID=' $LSB_RELEASE_BIN | cut -d'=' -f2)
elif [ -f "$OS_RELEASE_BIN" ] ; then
	DISTRIB_ID=$(grep '^ID=' $OS_RELEASE_BIN | cut -d'=' -f2)
else
	echo -e "\033[31mError: Could not determine your OS distribution.\e[0m"
	exit 1
fi

# to lower case
DISTRIB_ID=${DISTRIB_ID,,}
# keep only alphanumerical chars
DISTRIB_ID=$(echo $DISTRIB_ID | tr -cd [:alnum:])

if [ ! -x "$(which sudo)" ] ; then
	echo -e "\033[31mError: command \"sudo\" not found on your system.\e[0m"
	exit 1
fi

case $DISTRIB_ID in
	# Debian/Ubuntu family
	elementaryos|debian|ubuntu|linuxmint|raspbian)
		PACKAGE_INST='sudo apt-get install'
		PIP_PKG_NAME='python3-pip'
		PYGOBJECT_PKG_NAME='python3-gi'
		INOTIFY_PKG_NAME='inotify-tools'
		PYTHON_DEV_PKG_NAME='python3-dev'
		;;
	fedora)
		PACKAGE_INST='sudo yum install'
		PIP_PKG_NAME='python3-pip'
		PYGOBJECT_PKG_NAME='pygobject3'
		INOTIFY_PKG_NAME='inotify-tools'
		PYTHON_DEV_PKG_NAME='python3-devel'
		;;
	arch|archarm|manjarolinux)
		PACKAGE_INST='sudo pacman -S --needed'
		PIP_PKG_NAME='python-pip'
		PYGOBJECT_PKG_NAME='python-gobject'
		INOTIFY_PKG_NAME='inotify-tools'
		PYTHON_DEV_PKG_NAME=''
		;;
	opensuse)
		PACKAGE_INST='sudo zypper install'
		PIP_PKG_NAME='python3-pip'
		PYGOBJECT_PKG_NAME='python3-gobject'
		INOTIFY_PKG_NAME='inotify-tools'
		PYTHON_DEV_PKG_NAME='python3-devel'
		;;
	*)
		echo -e "\033[31mError: setup script does not support your distro token \e[1m$DISTRIB_ID\e[21m\e[0m."
		exit 1
		;;
esac

if [ ! -x "$(which python3)" ] ; then
	echo -e "\033[31mNotice: Python 3.x not found on the system.\e[0m"
	$PACKAGE_INST python3
else
	echo -e "\e[92mpython3 installed...OK\e[0m"
fi

$PACKAGE_INST $PYTHON_DEV_PKG_NAME

if [ ! -x "$(which pip3)" ] ; then
	echo -e "\033[31mNotice: pip3 not found on the system.\e[0m"
	$PACKAGE_INST $PIP_PKG_NAME
	if [ "$?" -ne 0 ] ; then
		echo -e "\033[31mNotice: it seems failed installing pip3 from package repository.\e[0m"
		echo -e "\e[96mInstall pip3 from source...\e[0m"
		wget https://bootstrap.pypa.io/get-pip.py && sudo python3 get-pip.py \
		    && rm get-pip.py && echo -e "\e[92mpip3 installed...OK\e[0m"
	fi
else
	echo -e "\e[92mpip3 installed...OK\e[0m"
fi

if [ ! -x "$(which inotifywait)" ] ; then
	echo -e "\e[91mNotice: installing inotifywait...\e[0m"
	$PACKAGE_INST $INOTIFY_PKG_NAME
else
	echo -e "\e[92minotifywait installed...OK\e[0m"
fi

$PACKAGE_INST $PYGOBJECT_PKG_NAME $INOTIFY_PKG_NAME

do_clean

# Register package
sudo python3 setup.py install

# Clean temporary files
sudo python3 setup.py clean

do_clean

# Create settings dir
rm -rf ~/.onedrive
mkdir ~/.onedrive
cp ./onedrive_d/res/default_ignore.ini ~/.onedrive/ignore_v2.ini

sudo touch /var/log/onedrive_d.log
sudo chown $CURRENT_USER /var/log/onedrive_d.log

echo -e "\e[92monedrive-d installed successfully.\e[0m"
echo -e "\e[92mPlease run command \`onedrive-pref\` to set up the program.\e[0m"
