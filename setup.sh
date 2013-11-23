SKYDRIVED_USER_DIR=".skydrive"
SKYDRIVED_USER_CONF="user.conf"

cd ~

if [ ! -d "$SKYDRIVED_USER_DIR" ]; then
	echo "Creating directory $SKYDRIVED_USER_DIR"
	mkdir $SKYDRIVED_USER_DIR
fi

if [ -f "$SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF" ]
then
	echo "The configuration file for SkyDrive-d already exists."
	read -n 1 -r -p "Would you like to overwrite the current data [y/n]? "
	echo ""	#initiate a new line.
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
		rm -vf "$SKYDRIVED_USER_DIR/$SKYDRIVED_USER_CONF"
	else
		echo "The current configuration is kept."
		echo "Setup will exit."
		exit 0
	fi
fi

cd "$SKYDRIVED_USER_DIR"

echo "WINDOWS_LIVE_ID=123@346.com" > $SKYDRIVED_USER_CONF
