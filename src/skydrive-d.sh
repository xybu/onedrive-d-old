#!/bin/bash

SKYDRIVED_USER_DIR=`eval "echo ~/.skydrive"`
SKYDRIVED_USER_CONF="user.conf"
SKYDRIVED_LOG_NEW="run_newest.log"
SKYDRIVED_LOG_LAST="run_last.log"

SKYDRIVED_ROOT_PATH=`grep "rootPath:" $SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF | cut -d ' ' -f2`

if [ -f "$SKYDRIVED_USER_DIR/$SKYDRIVE_LOG_NEW" ]
then
	mv "$SKYDRIVED_USER_DIR/$SKYDRIVE_LOG_NEW" "$SKYDRIVED_USER_DIR/$SKYDRIVE_LOG_LAST"
	ls $SKYDRIVED_ROOT_PATH -Rl --time-style "+%Y-%m-%dT%H:%M:%S"
else
	echo "No current log exists. Do you want to make a deep synchronization between SkyDrive server and your local directory \"$SKYDRIVED_ROOT_PATH\"?"
	echo " * Files that don't exist locally will be downloaded."
	echo " * Local Files that are newer than the server version will be uploaded."
	echo " * Local Files that are older than the server version will be replaced by the server version."
	read -n 1 -r -p "Proceed [y/n]? "
	echo ""	#initiate a new line.
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
		python synchronize.py
	fi
fi

eventBuffer=""

nohup inotifywait -e unmount,close_write,create,delete,delete_self,move --format "%e %f %w" -mr ~/SkyDrive | 
while IFS=' ' read event directory file
#while read line
do
	echo "$event $directory $file"
	case "$event" in
    	"MOVED_TO,ISDIR" )
    		echo "Directory $eventBuffer was moved to $file$directory."
    		eventBuffer=""
    		;;
    	"MOVED_FROM,ISDIR" )
    		eventBuffer="$file$directory"
    		;;
	esac
done
