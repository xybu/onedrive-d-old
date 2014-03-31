#!/bin/bash

# inst.sh
# 
# Install the pre-requisites for skydrive-d
# sudo permission required.
# 
# @author	Xiangyu Bu
# 

# function install_pkg $pkgName
install_pkg() {
	echo "Checking if package \"$1\" is installed..."
	query=`dpkg-query -l $1`
	if [ $? -eq 1 ]; then
		echo "Installing package $1..."
		sudo apt-get -y install $1
	else
		echo "Package $1 is installed. Skip this step."
	fi
}

echo "Installing / upgrading package \"dpkg\"..."
sudo apt-get -y install dpkg

# install Linux packages required for python-skydrive
install_pkg git
install_pkg python-pip
install_pkg libyaml-dev
install_pkg python-yaml
install_pkg python-dateutil
install_pkg python-urllib3

# install Linux packages required for skydrive-d
install_pkg inotify-tools

echo "install urllib3 pre-requisite for python-skydrive..."
sudo pip install urllib3 --upgrade
sudo pip install requests --upgrade

# install python-skydrive
#  Note that to install stuff in system-wide PATH and site-packages, 
#  privileges need to be elevated.
#  Use "install --user", ~/.pydistutils.cfg or
#  virtualenv to do unprivileged installs into custom paths.
echo "Installing/Upgrading python-skydrive..."
sudo pip install 'git+https://github.com/mk-fg/python-skydrive.git#egg=python-skydrive[standalone]' --upgrade

# patch python-skydrive to solve ImportError: no module PoolManager
# Issue URL: https://github.com/mk-fg/python-skydrive/issues/13
#TODO: suppose it is installed in /usr/local/lib/python2.7/dist-packages/skydrive/ for now...
echo "Patching python-skydrive for a potential bug..."
PYTHON_SKYDRIVE_PATH=/usr/local/lib/python2.7/dist-packages/skydrive
sudo sed -i 's/requests.packages.urllib3/urllib3/g' $PYTHON_SKYDRIVE_PATH/*.py
sudo rm -f $PYTHON_SKYDRIVE_PATH/*.pyc
echo "Successfully patched python-skydrive."

