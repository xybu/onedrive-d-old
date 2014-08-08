# onedrive-d

A Microsoft OneDrive client on Linux desktop environment, written in Py3k.

## Introduction

The branch `1.0-dev` will be rewritten, thereby finishing the features
that are unable or itchy to implement in old releases.

### TODO Lists

 - [ ] Live Connect REST API written in Py3k
 	 - [X] Get access token uri
 	 - [X] Get access token
 	 - [X] Refresh access token
 	 - [X] Sign out
 	 - [ ] Download a file
 	 - [ ] Upload a file
 	 - [ ] Update a file
 	 - [ ] Getting user data
 	 - [ ] Obtaining user consent
 	 - [ ] Read file property
 	 - [ ] Read folder property
 	 - [ ] Update file property
 	 - [ ] Update folder property
 	 - [ ] Get links to files and folders
 	 - [ ] Get the storage quota information
 	 - [ ] Get a list of shared files / folders
 	 - [ ] Move or copy a file or folder
 	 - [ ] Delete a file
 	 - [ ] Create a folder
 	 - [ ] Delete a folder
 	 - [ ] Get a list of most recently used documents
 	 - [ ] Traverse the OneDrive directory
 	 - [ ] Display a preview of an OneDrive item
 	 - [ ] Create an album
 	 - [ ] Update an album
 	 - [ ] Read an album
 	 - [ ] Delete an album
 	 - [ ] Read a tag
 	 - [ ] Create a tag
 	 - [ ] Delete a tag
 - [X] Support both GUI and command-line interfaces
 	 - [X] Command-line preference dialog
 	 - [ ] Gtk preference Dialog
 	 - [ ] Command-line observer
 	 - [ ] Gtk observer
 - [X] Easily customizable ignore list
 - [ ] Installation scripts

## Approaches

The program consists of two parts, *main* and *prefs*. Both parts can run with and without GUI The program can run with and without GUI.

The GUI library planned to use is `PyGI`.

## Installation

Run command `./setup.sh` (planned)

## Uninstallation

Run command `./setup.sh uninstall` (planned)

### Architecture

There are two entry points in the program: `onedrive-d` and `onedrive-pref`:

 * `onedrive-d` deals with synchronization.
 * `onedrive-pref` updates the preferences.

Both commands support two arguments: `--no-gui` (use command-line interface) and `--help` (list all supported arguments).

Besides, `onedrive-pref --log-out` will log out the current user.

#### onedrive-d

For `onedrive-d`, there are three major threads:

 * The *MainThread* initializes the process and communicates with OS.
 * The *daemon* thread syncs the local repository with the OneDrive server and issues events to its observers;
 * The *observer* thread observes and handles events from the daemon.
 	 * The observer may be hooked with either `default` or `gtk` event handlers, depending on the existence of `--no-gui`.

#### onedrive-pref

## Reference Environment

The program is tested on latest Xubuntu 64-bit and should work on other Debian/Ubuntu variants.

## Contact

Xiangyu Bu