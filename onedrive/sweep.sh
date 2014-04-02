#!/bin/bash

ps -e | grep onedrive-d | cut -d' ' -f2 | xargs kill -9
# killall onedrive-d -v
ps -e | grep inotifywait | cut -d' ' -f2 | xargs kill -9
# killall inotifywait -v
