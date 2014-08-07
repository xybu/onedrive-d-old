# onedrive-d

A Microsoft OneDrive client on Linux desktop environment.

## Introduction

The branch `1.0-dev` will be rewritten, thereby finishing the features
that are unable or itchy to implement in old releases.

## Approaches

The program consists of two parts, *main* and *prefs*. Both parts can run with and without GUI The program can run with and without GUI.

The GUI library planned to use is `wxPython`.

### Multi-threading

The main process has two threads that work like client-server architecture.
 * The *daemon* thread syncs the local repository with the OneDrive server and writes information to database;
 * The *gui* thread provides a status icon and shows notifications.

#### Daemon Thread

The Daemon thread may create some helper threads.

#### GUI Thread

## Reference Environment

The program is tested on latest Xubuntu 64-bit and should work on other Debian/Ubuntu variants.

## Contact

Xiangyu Bu