#!/bin/bash

# setup.sh
# 
# Install the daemon on the running computer.
# sudo permission required.
# 
# @author	Xiangyu Bu
# @update	Mar 02, 2014


# The actual user who executes the script
ONEDRIVED_ACTUAL_USER="$SUDO_USER"
if [ "${#ONEDRIVED_ACTUAL_USER}" -eq "0" ]; then
	ONEDRIVED_ACTUAL_USER="$USER"
fi

# Application configuration directory
ONEDRIVED_CONF_PATH="$HOME/.onedrive"


# skydrive-d configuration file path
ONEDRIVED_CONF_FILE="$ONEDRIVED_CONF_PATH/user.conf"

# function build_lcrc $path
# writes the lcrc configuration file
build_lcrc() {
	echo "The directory \"$1\" will be in sync with your OneDrive."
	echo -e "client:" >> "$HOME/.lcrc"
	echo -e "  id: 000000004010C916" >> "$HOME/.lcrc"
	echo -e "  secret: PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi" >> "$HOME/.lcrc"
	chown $ONEDRIVED_ACTUAL_USER $HOME/.lcrc
	echo -e "rootPath: $1" >> $ONEDRIVED_CONF_FILE
}

# function install_prerequisites
# prompt for install the pre-requisite packages
install_prerequisites() {
	read -n 1 -r -p "Would you like to install prerequisite packages to your system? [y/n] "
	echo ""
	if [[ $REPLY =~ ^[Yy]$ ]] ; then
		sudo ./inst_pre_requisites.sh
	fi
}

# function if_make_dir $dirPath
# mkdir if it does not exist
if_make_dir() {
	if [ ! -d "$1" ] ; then
		echo "Creating directory $1"
		mkdir $1
	fi
}

# function exec_cli_auth
# authenticate skydrive-cli
exec_cli_auth() {
	skydrive-cli auth
}

# install pre-requisites
install_prerequisites

# make conf dir
if_make_dir $ONEDRIVED_CONF_PATH

# check if configuration file needs to be rebuilt
reset_conf_flag=0
if [ -f "$ONEDRIVED_CONF_FILE" ]
then
	echo "The configuration file for skydrive-d already exists."
	read -n 1 -r -p "Would you like to overwrite the current configurations? [y/n] "
	echo ""	# initiate a new line.
	if [[ $REPLY =~ ^[Yy]$ ]] ; then
		reset_conf_flag=1
	fi
else
	reset_conf_flag=1
fi

# rebuild conf file if needed
if [ "$reset_conf_flag" -eq 1 ] ; then
	rm -vf "$HOME/.lcrc" "$ONEDRIVED_CONF_FILE"
	echo "Specify the directory to synchronize with OneDrive [$HOME/OneDrive][ENTER]:"
	read -r ONEDRIVE_DIR
	#If no user input, lets default to home directory
	if [ -z $ONEDRIVE_DIR ]; then
		ONEDRIVE_DIR=$HOME/OneDrive
	fi
	if_make_dir $ONEDRIVE_DIR
	build_lcrc $ONEDRIVE_DIR
else
	echo "The current configurations were kept."
	ONEDRIVE_DIR=`grep "rootPath:" $HOME/.onedrive/user.conf | cut -d ' ' -f2`
fi

# ask for authentication
read -n 1 -r -p "Would you like to authenticate the client now? [y/n] "
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	exec_cli_auth
	until [ $? -eq 0 ]; do
		read -n 1 -r -p "Authentication failed. Would you like to retry? [y/n] "
		echo ""
		if [[ $REPLY =~ ^[Yy]$ ]] ; then
			exec_cli_auth
		fi
	done
else
	echo -e "You can execute the command \"skydrive-cli auth\" to authentication later."
fi

if_make_dir $ONEDRIVE_DIR

chown -R $ONEDRIVED_ACTUAL_USER $ONEDRIVE_DIR
chown -R $ONEDRIVED_ACTUAL_USER $ONEDRIVED_CONF_PATH

# start daemon
read -n 1 -r -p "Would you like to start onedrive-d now? [y/n] "
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	# change the owner of the folder to the actual user, in case the user sudos
	cd ./src/
	./onedrive-d
	:
else
	echo -e "You choose to start onedrive-d later."
	echo "Setup was completed."
fi
