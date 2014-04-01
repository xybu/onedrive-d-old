onedrive-d
==================

**This is the Working-in-Progress branch which is under serious reconstruction.**

Description
-----------
This project intends to develop an OneDrive (formerly SkyDrive) daemon on (X)ubuntu written in Python.

The program is a higher-level abstraction of the project `python-skydrive` (https://github.com/mk-fg/python-skydrive) by Mike Kazantsev.

Besides the `python-skydrive` base, there are a few major components in the project:

 * **DirScanner** scans the differences between the local and remote `dir`s, and merges them if needed
 	 * It does not delete files.
 	 * May undo file deletion or mess up the repo. But by far we prefer the safest approach.
 * **TaskWorker**
 	 * It executes the tasks issued by DirScanner objects
 	 * and waits to handle new tasks
 	 	 * **Tasks** are wrapped as objects
 * **LocalMonitor**
 	 * It forks a `inotifywait` process to monitor the OneDrive local repository.
 	 * and issue tasks for TaskWorkers to perform if there are any changes detected.
 * **RemoteMonitor**
 	 * Periodically gets the most recently changed files from OneDrive server _(planned)_
 	 * more at http://isdk.dev.live.com/dev/isdk/ISDK.aspx?category=scenarioGroup_skyDrive&index=6
 * **Linux Service**
 	 * A script that binds the python program to init.d
 	 * uses `start-stop-daemon` as the service interface _(planned)_

Notice
--------

* (April 1, 2014, by XB) The program in `wip` branch is now functional. More tests and polishments are needed.

* (Mar 30, 2014, by XB) If you encountered an `ImportError` when python imports `PoolManager()`, please use the `inst_pre_requisite.sh` in **wip** branch which patched the problem for now.
	 * Update `python-requests` package can also solve the problem.
	 * The issue is tracked at https://github.com/mk-fg/python-skydrive/issues/13.

Installation
--------------
__The file is to be rewritten.__

Execute the command: `sudo ./setup.sh` to install the daemon.

Homepage
-----------
Please visit: http://www.xybu.me/projects/skydrive-d/


Contact
--------
Xiangyu Bu (http://xybu.me or drop me email: xybu92(at)live.com)
