Account Management
==================

Each Linux user will have one onedrive-d daemon process that synchronizes all the OneDrive accounts the user authenticates. The process runs as onedrive user and onedrive group.

User account information is stored in `/etc/onedrived/` directory owned by root. This way only the root user can read or modify the sensitive tokens of OneDrive accounts. Correspondingly, onedrive-d process starts as root user and drops privilege to the real user after reading the config information.
