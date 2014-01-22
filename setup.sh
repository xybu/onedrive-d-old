#!/bin/bash

# setup.sh
# 
# Install the daemon on the running computer.
# sudo permission required.
# 
# @author	Xiangyu Bu
# @update	Jan 08, 2014

# Home Directory
HOMEDIR=`eval echo ~${SUDO_USER}`

# Application configuration directory
SKYDRIVED_CONF_PATH="$HOMEDIR/.skydrive"

# skydrive-d configuration file path
SKYDRIVED_CONF_FILE="$SKYDRIVED_CONF_PATH/user.conf"

# function build_lcrc $path
# writes the lcrc configuration file
build_lcrc() {
	echo "The directory \"$1\" will be in sync with your SkyDrive."
	echo -e "client:" >> "$HOMEDIR/.lcrc"
	echo -e "  id: 000000004010C916" >> "$HOMEDIR/.lcrc"
	echo -e "  secret: PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi" >> "$HOMEDIR/.lcrc"
	echo -e "rootPath: $1" >> $SKYDRIVED_CONF_FILE
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
if_make_dir $SKYDRIVED_CONF_PATH

# check if configuration file needs to be rebuilt
reset_conf_flag=0
if [ -f "$SKYDRIVED_CONF_FILE" ]
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
	rm -vf "$HOMEDIR/.lcrc" "$SKYDRIVED_CONF_FILE"
	echo "Specify the directory to synchronize with SkyDrive [$HOMEDIR/SkyDrive][ENTER]:"
	read -r SKYDRIVE_DIR
	if_make_dir $SKYDRIVE_DIR
	build_lcrc $SKYDRIVE_DIR
else
	echo "The current configurations were kept."
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

# start daemon
read -n 1 -r -p "Would you like to start skydrive-d now? [y/n] "
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	./skydrive-d
else
	echo -e "You choose to start skydrive-d later."
fi
