onedrive-d
==========

**FUTURE VERSION. DO NOT TRY.**

## Installation

(1) Always uninstall older versions before installing newer ones

```bash
# To remove onedrive-d < 1.0
pip uninstall onedrive_d
# To remove onedrive-d >= 1.0
pip3 uninstall onedrive_d

# Remove residual config files
rm -rfv ~/.onedrive
```

(2) Grab the source code

```bash
git clone https://github.com/xybu/onedrive-d.git
cd onedrive-d
```

(3) Run `setup.sh`

```bash
./setup.sh inst
```

## Removal

Refer to step 1 of section "Installation".

## Multi-Threading

The jobs of threads of main program are planned as follows:

 * `MainThread`: if GUI is enabled, for GUI responsiveness; 
   for CLI case, used for heart-beating.
 * `thread_manager`: checking network condition if any other threads are put to sleep
   under its queue, and when network _seems_ fine wake up the threads; blocked otherwise.
