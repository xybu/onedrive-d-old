onedrive-d
==========

A Microsoft OneDrive desktop client / daemon on Linux, written in Python 3.

## Note for this branch

This branch experiments with daemonization of onedrive-d process.

## Install

Steps 1, 2, and 5 need to be done manually. For steps 3 and 4, the script file `install.sh` will handle the work automatically.

(1) Always uninstall older versions before installing newer ones

```bash
# To remove onedrive-d < 1.0
sudo pip uninstall onedrive_d
# To remove onedrive-d >= 1.0
sudo pip3 uninstall onedrive_d

# Remove residual config files
rm -rfv ~/.onedrive
```

(2) Grab the source code

```bash
git clone https://github.com/xybu/onedrive-d.git
cd onedrive-d
```

Or you can browse https://github.com/xybu/onedrive-d and download the ZIP file manually.

(3) Pre-requisites

Your local filesystem must store UTC timestamps, not local time. This is true
for most Unix filesystems.

onedrive-d requires Python3 intepreter. If Python version is older than 3.4, `python3-pip` is also required.

For GUI component to work, Python3 binding of GObject (`python3-gi` package for Debian/Ubuntu, `pygobject3` for Fedora, `python-gobject` for Arch, and `python3-gobject` for OpenSUSE) is needed. [Refer to this article if you want to build PyGObject from source.](https://python-gtk-3-tutorial.readthedocs.org/en/latest/install.html)

Another recommended package is `inotify-tools` (for most package managers), which contains command `inotifywait`. If this command is available on the system, the real-time file system monitoring thread will be enabled. Otherwise the synchronization is performed every certain amount of time (configurable).

(4) Install onedrive-d

```bash
# Register package
sudo python3 ./onedrive_d/setup.py install

# Clean temporary files
sudo python3 ./onedrive_d/setup.py clean

# Create settings dir
mkdir ~/.onedrive
cp ./onedrive_d/res/default_ignore.ini ~/.onedrive/ignore_v2.ini

# Create log file
sudo touch /var/log/onedrive_d.log
# you may need to change `whoami` to your username
sudo chown `whoami` /var/log/onedrive_d.log
```

(5) Configure / start onedrive-d

```bash
# First read help info
onedrive-pref --help
onedrive-d --help

# Run config program with CLI
onedrive-pref
# Or run with GUI
onedrive-pref --ui=gtk

# Run onedrive-d
# start as a daemon
onedrive-d start
# or start as a regular process
onedrive-d start --debug
```

## Run without installation

To run the source code directly without installing it to the system,
do steps 1 to 3 in *Installation* section, and copy config files by

```bash
mkdir ~/.onedrive
cp ./onedrive_d/res/default_ignore.ini ~/.onedrive/ignore_v2.ini
```

Now you can run the program by commands

```bash
# assume you are in "onedrive-d" folder that contains "onedrive_d" folder.

# equivalent to `onedrive-pref` command
python3 -m onedrive_d.od_pref --help

# equivalent to `onedrive-d` command
python3 -m onedrive_d.od_main --help
```

Note that the commands above are no longer valid after installing the package to the system.

## Remove

Refer to step 1 of section "Installation".

## Notes for Users

### Data Integrity

 * Files and directories "deleted" locally can be found in Trash.
 * Files and directories "deleted" remotely can be found in OneDrive recycle bin.
 * Files overwritten remotely can be recovered by OneDrive file version feature.
 * onedrive-d only performs overwriting when it is 100% sure one file is older than its local/remote counterpart.

### Uploading / Downloading by Blocks

When file size exceeds an amount (e.g., 8 MiB), onedrive-d will choose to upload / download it by blocks of smaller size (e.g., 512 KiB). This results in smaller cost (thus better reliability) when recovering from network failures, but more HTTP requests may slow down the process. Tweak the parameters to best fit your network condition.

### Copying and Moving Files and Folders

Because the various behaviors of file managers on Linux, it is hard to determine what actions a user performed based on the log of `inotifywait`. We adopt a very conservative strategy to judge if a file is moved within local OneDrive folder. In most cases file moving results in removing the old path and uploading to the new path. This kinds of wastes network traffic.

Most file managers, including `cp` command, do not copy file attributes like mtime. `inotifywait` reports file writing on copy completion. This makes it infeasible to check if the file writing is a "copy" action. As a result, file copying is also treated as uploading.

Things are even worse when one copies / moves a directory. In most cases the mtime attribute will be changed, resulting in onedrive-d uploading the whole folder.
