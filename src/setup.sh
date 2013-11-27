SKYDRIVED_USER_DIR=".skydrive"
SKYDRIVED_USER_CONF="user.conf"

HOMEDIR=`eval "echo ~$USERNAME"`
SKYDRIVED_USER_DIR="$HOMEDIR/$SKYDRIVED_USER_DIR"
SKYDRIVED_CONF_PATH="$SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF"

read -n 1 -r -p "Would you like to install python-skydrive and required components to your system [y/n]? "
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	./inst.sh
fi

if [ ! -d "$SKYDRIVED_USER_DIR" ]; then
	echo "Creating directory $SKYDRIVED_USER_DIR"
	mkdir $SKYDRIVED_USER_DIR
fi

if [ -f "$SKYDRIVED_CONF_PATH" ]
then
	echo "The configuration file for SkyDrive-d already exists."
	read -n 1 -r -p "Would you like to overwrite the current configurations [y/n]? "
	echo ""	#initiate a new line.
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
		rm -vf "$HOMEDIR/.lcrc" "$SKYDRIVED_CONF_PATH"
		echo "Specify the directory to synchronize with SkyDrive [$HOMEDIR/SkyDrive][ENTER]:"
		#read -r -p "" SKYDRIVE_DIR
		read -r SKYDRIVE_DIR
		echo "The directory \"$SKYDRIVE_DIR\" will be in sync with your SkyDrive."
		echo -e "client:" >> "$HOMEDIR/.lcrc"
		echo -e "  id: 000000004010C916" >> "$HOMEDIR/.lcrc"
		echo -e "  secret: PimIrUibJfsKsMcd0SqwPBwMTV7NDgYi" >> "$HOMEDIR/.lcrc"
		echo -e "rootPath: $SKYDRIVE_DIR" >> $SKYDRIVED_CONF_PATH
	else
		echo "The current configurations were kept."
	fi
fi

read -n 1 -r -p "Would you like to authenticate python-skydrive [y/n]? "
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
	skydrive-cli auth
fi

echo "Setup will now synchronize the local repository with SkyDrive server..."
#./utils.sh fullSync
