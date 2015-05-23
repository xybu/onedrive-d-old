Account Management
==================

Each Linux OS user will have exactly ONE onedrive-d daemon process that synchronizes all the OneDrive accounts the user authenticates. But note that each OS user can link more than one OneDrive account for onedrive-d program to sync.

User account information is stored in `/etc/onedrived/` directory owned by root. This way only the root user can read or modify the sensitive tokens of OneDrive accounts. Correspondingly, onedrive-d process starts as root user and drops privilege to the real user after reading the config information. At exit time the program will raise privilege to write the changes to disk.

## User Database

Each OS user has her / his own onedrive-d SQLite database. For example, a user whose uid is `1000` may have her database file at `/etc/onedrived/1000.db`, while another user whose uid is `1002` may have his database file at `/etc/onedrived/1002.db`.

There are three tables in each database:

 * `accounts` - stores the information of all accounts linked to the OS user.
 * `config` - stores the parameters and values OS user gives onedrive-d program. 
 * `entries` - stores all the records of files and directories onedrive-d should keep track of.

### Account Info

### Config

### Entries
