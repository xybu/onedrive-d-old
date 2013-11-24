#!/bin/bash
#utils.sh [fullSync]

SKYDRIVED_USER_DIR=".skydrive"
SKYDRIVED_USER_CONF="user.conf"

HOMEDIR=`eval "echo ~$USERNAME"`
SKYDRIVED_USER_DIR="$HOMEDIR/$SKYDRIVED_USER_DIR"
SKYDRIVED_CONF_FULLPATH="$SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF"

if [ "$1" = "" ]; then
	echo "Usage:"
	echo "./utils.sh [fullSync|TODO]"
	exit 0
fi

if [ "$1" = "fullSync" ]; then
	echo "Starting full sync with SkyDrive server..."
	skydrive-cli tree > "$SKYDRIVED_USER_DIR/skydrive.tree"
	exit 0
fi
