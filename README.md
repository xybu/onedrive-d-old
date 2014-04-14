onedrive-d
==================
This project intends to develop a client program for Microsoft OneDrive 
(formerly SkyDrive) on Ubuntu-based Linux. The API is based on Mike Kazantsev's 
project [*python-onedrive*](https://github.com/mk-fg/python-onedrive).

	 * While you can use `onedrive-cli` command offered by *python-onedrive* 
	 project, the daemon tries to do the work automatically, and GUIs are being 
	 developed.
	 
	 * The reference environment is Ubuntu, but by installing the corresponding 
	 packages required by the project, it should work on other Linux distros.

## Branches
 * **master**: the main branch
 * **wip**: the newest work

For Developers
--------------

## Components

The major components in this program are:

 * **DirScanner** scans the differences between the local and remote `dir`s, and
  merges them if needed
 	 * It does not delete files.
 	 * May undo file deletion or mess up the repo. But by far we prefer the 
 	 safest approach.
 * **TaskWorker**
 	 * It executes the tasks issued by DirScanner objects
 	 * and waits to handle new tasks
 	 	 * **Tasks** are wrapped as objects
 * **LocalMonitor**
 	 * It forks a `inotifywait` process to monitor the OneDrive local 
 	 repository.
 	 * and issue tasks for TaskWorkers to perform if there are any changes 
 	 detected.
 * **RemoteMonitor**
 	 * Pull the recent updates from server and merge the new ones 
 	 * Periodically update the quota information
 * **Linux Service**
 	 * The service will be installed to `/etc/init.d/onedrive-d`

For Users
---------

## Installation

 - Download the source from GitHub repo
 - In the source directory, run `sudo ./inst install` and go with the prompts
 - If the daemon fails to register, you may run `onedrive-d` command to have the
  daemon start
 
 Notes:
 
 Since the package is still under development, it will not run at system 
 startup.


More Links
----------

## Links
 * Project introduction page: http://xybu.me/projects/onedrive-d

## Contact
 * [Xiangyu Bu](http://xybu.me)
