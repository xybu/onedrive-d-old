Error Dictionary
================

This document lists and explains all error messages onedrive-d may return.

Each error message has the format `error_message (id).` where `id` is either a number like `001` or a number like `001.1` (the number after the dot is given by OS). To look up an error, search for the major error number (e.g., `001`) in this page.

# Init-time error

`onedrive-d daemon must run as root (001).` Please run the daemon as root user. After the sensitive OneDrive account information of real OS user is loaded, the privilege will be dropped.

`onedrive-d daemon cannot find the real login user (002).` The environment variable `SUDO_UID` does not exist and therefore onedrive-d cannot figure out which user is behind root.

`User "XXX" (ddd) has not configured onedrive-d (003).` The user whose username is `XXX` and user id is `ddd` has not set up the daemon. Run the preference tool to initialize the user-specific configurations, link OneDrive accounts, etc.

`Failed to drop root privilege - {REASON} (004.{ERRNO}).` OS does not permit dropping root privilege somehow. Refer to `{REASON}` and `{ERRNO}` for what OS says.

# Preference CLI

`Failed to create directory "/etc/onedrived" as root - {REASON} (005.{ERRNO}).` Cannot create the account inventory directory. Refer to `{REASON}` and `{ERRNO}` for what OS says.

`Failed to create config dir - {REASON} (006.{ERRNO}).` Please check why the directory `~/.onedrive` cannot be created.
