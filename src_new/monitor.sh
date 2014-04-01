#!/bin/bash

# The monitor script to keep track of changes in OneDrive local repo.
# 
# @author	Xiangyu Bu

moveFrom_buffer=""

# Use inotifywait to monitor file system changes
nohup inotifywait -e unmount,close_write,create,delete,delete_self,move --format "%e %f %w" -mr $ONEDRIVED_ROOT_PATH | 
while IFS=' ' read event f1 f2
do
	# the fields may not be exactly "event dir file"
	echo "$event $f1 $f2"
	case "$event" in
		"MOVED_FROM,ISDIR" )
			moveFrom_buffer="$f2$f1"
			;;
		"MOVED_TO,ISDIR" )
			# execute the dir move function
			echo $event $moveFrom_buffer $f2$f1
			moveFrom_buffer="" # clear buffer
			;;
		"CLOSE_WRITE,CLOSE" )
			echo $event $f1 $f2
			;;
		"CREATE,ISDIR" )
			# create a directory
			echo $event $f1 $f2
			;;
		"DELETE" )
			# file deletion
			echo $event $f1 $f2
			;;
		"DELETE,ISDIR" )
			# delete a directory
			echo $event $f1 $f2
			;;
	esac
done
