SKYDRIVED_USER_DIR=".skydrive"
SKYDRIVED_USER_CONF="user.conf"

HOMEDIR=`eval "echo ~$USERNAME"`
SKYDRIVED_USER_DIR="$HOMEDIR/$SKYDRIVED_USER_DIR"
SKYDRIVED_CONF_FULLPATH="$SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF"

if [ ! -d "$SKYDRIVED_USER_DIR" ]; then
	echo "Creating directory $SKYDRIVED_USER_DIR"
	mkdir $SKYDRIVED_USER_DIR
fi

if [ -f "$SKYDRIVED_CONF_FULLPATH" ]
then
	echo "The configuration file for SkyDrive-d already exists."
	read -n 1 -r -p "Would you like to overwrite the current configurations [y/n]? "
	echo ""	#initiate a new line.
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
		rm -vf "$HOMEDIR/.lcrc"
		echo "client:" >> "$HOMEDIR/.lcrc"
		echo -e "  id: 000000004010C916" >> "$HOMEDIR/.lcrc"
		echo -e "  secret: PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi" >> "$HOMEDIR/.lcrc"
		rm -vf "$SKYDRIVED_CONF_FULLPATH"
		read -r -p "Specify the directory to synchronize with SkyDrive [$HOMEDIR/SkyDrive][ENTER]: " SKYDRIVE_DIR
		echo "The directory \"$SKYDRIVE_DIR\" will be in sync with your SkyDrive."
		echo "SKYDRIVE_DIR=$SKYDRIVE_DIR" >> $SKYDRIVED_CONF_FULLPATH
	else
		echo "The current configuration is kept."
	fi
fi

echo "Setup will now synchronize the local repository with SkyDrive server..."
./utils.sh fullSync
