Account Management
==================

Each Linux OS user will have exactly ONE onedrive-d daemon process that synchronizes all the OneDrive accounts the user authenticates. But note that each OS user can link more than one OneDrive account for onedrive-d program to sync.

For security concern, all account information and config information are stored as root. One must have root privilege to read or modify them.

User config information is stored in `~/.onedrive/` directory owned by root.

User account information is stored in `/etc/onedrived/` directory owned by root. This way only the root user can read or modify the sensitive tokens of OneDrive accounts. Correspondingly, onedrive-d process starts as root user and drops privilege to the real user after reading the config information. Before exiting, the program will raise privilege to write the changes to disk.

## Configuration File

User-specific configuration is stored in file `~/.onedrive/settings_v1.ini`.

The sections, keys, explanations, and default values are documented as follows:

### Intervals

`Intervals` section contains all keys that specify an interval of time.

|         Key            | Description | Default Value |
| ---------------------- | ------------------------------------------------------------------------------------- | ------------- |
| NETWORK_RETRY_INTERVAL | The amount of time, in sec, to wait before retry in face of a network failure.        | 20            |

## User Database

Each OS user has her / his own onedrive-d SQLite database. For example, a user whose uid is `1000` may have her database file at `/etc/onedrived/1000.db`, while another user whose uid is `1002` may have his database file at `/etc/onedrived/1002.db`.

There are two tables in each database:

 * `accounts` - stores the information of all accounts linked to the OS user.
 * `entries` - stores all the records of files and directories onedrive-d should keep track of.

### Account Info

### Entries
