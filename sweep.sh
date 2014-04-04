#!/bin/bash

# This is a script used to kill processes left when testing the code.

killall -9 onedrive-daemon
killall -9 inotifywait
killall -9 python
