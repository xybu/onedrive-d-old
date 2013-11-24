#!/bin/bash
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
