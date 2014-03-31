onedrive-d
==================

**This is the Working-in-Progress branch which is under serious reconstruction.**

Description
-----------
This project intends to develop an OneDrive (formerly SkyDrive) daemon on (X)ubuntu with mainly Bash script and Python.
The server-client interaction component is based on `python-skydrive` (https://github.com/mk-fg/python-skydrive) by Mike Kazantsev.

Besides the `python-skydrive` base, there are two (three?) major components in the project:
 * A python script that merges the remote OneDrive repository with the local repository.
 	 * No file will be deleted, and all files and dirs will be in sync when the merge part finishes execution.
 	 * May undo file deletion or mess up the repo. But by far we prefer the safest approach.
 * A bash script daemon that will monitor the local repo, and perform on remote repo the change when there is any.
 * A bash script daemon that periodically pulls the changes from server to local (planned).
 	 * The algorithm must be carefully thought of, as there is no hook (not found yet) that lets OneDrive server tells a client there are remote changes.
 	 * Periodically get the most recently changed files from server API, more at http://isdk.dev.live.com/dev/isdk/ISDK.aspx?category=scenarioGroup_skyDrive&index=6

Notice
--------
* (Mar 30, 2014, by XB) If you encountered an `ImportError` when python imports `PoolManager()`, please use the `inst_pre_requisite.sh` in **wip** branch which patched the problem for now.
	 * The issue is tracked at https://github.com/mk-fg/python-skydrive/issues/13

Installation
--------------
__Please beware that the program is extremely premature to use in real life scenario.__

Execute the command: `sudo ./setup.sh` to install the daemon.


File Description
------------------

`setup.sh`:
    The installation script. Sudo permission required.

`inst_pre_requisites.sh`:
	The script to install python-skydrive and its pre-requisite packages

`onedrive-d`:
	The daemon itself

`synchronize.py`:
	The synchronizer

`entries.py`:
	Class definitions for file and directory entries

Homepage
-----------
Please visit: http://www.xybu.me/projects/skydrive-d/


Contact
--------

Xiangyu Bu
