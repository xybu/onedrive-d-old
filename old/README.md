onedrive-d
==================
This project aims to deliver a Microsoft OneDrive (formerly SkyDrive) client that runs on major Linux distros. The API is based on Mike Kazantsev's 
project [*python-onedrive*](https://github.com/mk-fg/python-onedrive).

Currently the reference environment is Ubuntu x64, while support for RHEL/CentOS/Fedora is on the way.

## Branches
 * **master**: the main branch
 * **wip**: the newest work

For Users
---------

## Installation

 - Download or `git clone` the source from GitHub repo
 - In the source directory, run `./inst install` and go with the prompts
 - If you are upgrading from a previous version, run `./inst reinstall` instead
 - If the daemon fails to register, you may run `onedrive-d` command to start the
 
 Notes:
 
 Since the package is still under development, it will not run at system 
 startup.

## Usage

 * To start the daemon manually, issue command `onedrive-d`
 * To configure the program, issue command `onedrive-prefs`
 * To use the command-line tools, issue command `onedrive-cli` for more details

## Notes for RHEL / CentOS / Fedora Users

I've decided to support RHEL / CentOS / Fedora distros, and there are many tests to be done. Please do give me feedback. I really appreciate your help.

### How can I find the "Tray Icon" of OneDrive-D on Fedora?

On Fedora Gnome 20, press Super + M (default keyboard shortcut) to call out the _messaging tray_ and you will find the familiar OneDrive cloud icon in it.

## Notes about Usage

There are some notes regarding the usage.

* OneDrive uses NTFS file naming rules. i.e., case insensitive, and the following characters are reserved in file names: `<`, `>`, `:`, `"`, `\`,`/`, `|`, `?`, and `*`. As a result, files containing those special characters will be ignored by the program. As for case insensitivity, the program will rename files that conflict in cases.

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



More Links
----------

## Links
 * Project introduction page: http://xybu.me/projects/onedrive-d

## Contact
 * [Xiangyu Bu](http://xybu.me)
