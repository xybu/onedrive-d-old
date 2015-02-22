onedrive-d
==========

**FUTURE VERSION. DO NOT TRY.**

## Installation

Steps 1, 2, and 5 need to be done manually. For steps 3 and 4, there is a script file `install.sh` which run the commands automatically.

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

(3) Install pre-requisite packages

onedrive-d requires Python3 intepreter. If Python version is older than 3.4, `python3-pip` is also required.

For GUI component to work, Python3 binding of GObject (`python3-gi` package for Debian/Ubuntu, `pygobject3` for Fedora, `python-gobject` for Arch, and `python3-gobject` for OpenSUSE) is needed. (Refer to this article if you want to build PyGObject from source.)[https://python-gtk-3-tutorial.readthedocs.org/en/latest/install.html]

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

# Run onedrive-d (not daemonized yet)
onedrive-d
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
# equivalent to `onedrive-pref` command
python3 -m onedrive_d.od_pref

# equivalent to `onedrive-d` command
python3 -m onedrive_d.od_main
```

Note that the commands above are no longer valid after installing the package to the system.

## Removal

Refer to step 1 of section "Installation".

## Multi-Threading

The jobs of threads of main program are planned as follows:

 * `MainThread`: if GUI is enabled, for GUI responsiveness; 
   for CLI case, used for heart-beating.
 * `thread_manager`: checking network condition if any other threads are put to sleep
   under its queue, and when network _seems_ fine wake up the threads; blocked otherwise.
