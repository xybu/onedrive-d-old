#!/usr/bin/python

import os, sys, pwd, yaml, subprocess, platform

HOME_PATH = os.path.expanduser('~'+os.getenv("SUDO_USER"))


OS_USER = os.getenv("SUDO_USER")
if OS_USER == None or OS_USER == "":
	# the user isn't running sudo
	OS_USER = os.getenv("USER")


OS_DIST =  platform.linux_distribution()

def queryUser(question, answer = "y"):
	valid = {"y": True, "ye": True, "yes": True,
			 "n": False, "no": False}
	if answer == "y":
		prompt = " [Y/n] "
	elif answer == "n":
		prompt = " [y/N] "
	else:
		prompt = " [y/n] "
	
	sys.stdout.write(question + prompt)
	while True:
		response = raw_input().lower()
		if answer is not None and response == "":
			return answer
		elif response in valid.keys():
			return valid[response]
		else:
			sys.stdout.write("Please respond with 'y' (yes) or 'n' (no).\n")

def mkdirIfMissing(path):
	try:
		if path == "":
			print "The specified path is empty string."
			return False
		if not os.path.exists(path):
			os.mkdir(path, 0700)
			os.chown(path, pwd.getpwnam(OS_USER).pw_uid, pwd.getpwnam(OS_USER).pw_gid)
			print "Created directory \"" + path + "\"."
		return True
	except OSError as e:
		print "OSError({0}): {1}".format(e.errno, e.strerror)
		return False

def checkOSVersion():
	if OS_DIST[0] != "Ubuntu":
		if not queryUser("The package may not support non-Ubuntu based Linux.\nDo you still want to proceed?", "n"):
			print "Stopped."
			sys.exit(0)

def setupDaemon():
	rootPath = ""
	
	print "Setting up OneDrive-d..."
	
	assert mkdirIfMissing(HOME_PATH + "/.onedrive"), "Failed to create the configuration path."
	
	exclusion_list = []
	
	if queryUser("Do you want to exclude some files from being synchronized? ", "y"):
		if queryUser("\t1. Exclude Windows temporary files like \"Desktop.ini?\"", "y"):
			exclusion_list = exclusion_list + "~\$.*\.*|.*\.laccdb|Desktop\.ini|Thumbs\.db|EhThumbs\.db".split("|")
		if queryUser("\t2. Exclude typical Linux temporary files?", "y"):
			exclusion_list = exclusion_list + ".*~|\.lock".split("|")
		if queryUser("\t3. Exclude ViM temporary files?", "y"):
			exclusion_list = exclusion_list + ".netrwhist|\.directory|Session\.vim|[._]*.s[a-w][a-z]|[._]s[a-w][a-z]|.*\.un~".split("|")
		if queryUser("\t4. Exclude emacs temporary files?", "y"):
			exclusion_list = exclusion_list + "\#.*\#|\.emacs\.desktop|\.emacs\.desktop\.lock|.*\.elc|/auto-save-list|\.\#.*|\.org-id-locations|.*_flymake\..*".split("|")
		if queryUser("\t5. Exclude possibly Mac OS X temporary files?", "y"):
			exclusion_list = exclusion_list + "\.DS_Store|Icon\r|\.AppleDouble|\.LSOverride|\._.*|\.Spotlight-V100|\.Trashes".split("|")
		
		if exclusion_list != []:
			exclusion_list = "exclude: ^(" + "|".join(exclusion_list) + ")$\n"
		else:
			exclusion_list = "exclude: \"\""
			print "There is nothing in the exclusion list."
	else:
		exclusion_list = "exclude: \"\""
		print "Skipped."
	
	while True:
		sys.stdout.write("Please specify the local directory of OneDrive (default:" + HOME_PATH + "/OneDrive):\n")
		response = raw_input().strip()
		if response == None or response == "\n" or response == "":
			response = HOME_PATH + "/OneDrive"
		if mkdirIfMissing(response):
			CONF_PATH = HOME_PATH + "/.onedrive/user.conf"
			f = open(CONF_PATH, "w")
			rootPath = os.path.abspath(response)
			f.write("rootPath: " + rootPath + "\n")
			f.write(exclusion_list)
			f.write("confVer: 0.7\n")
			f.close()
			os.chown(CONF_PATH, pwd.getpwnam(OS_USER).pw_uid, pwd.getpwnam(OS_USER).pw_gid)
			os.chmod(CONF_PATH, 0600)
			break
		else:
			sys.stdout.write("Failed to create the directory \"" + response + "\". Please specify another one.\n")
	
	sh = """
#!/bin/sh

### BEGIN INIT INFO
# Provides:          onedrive-d
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

DAEMON_NAME=onedrive-d
DAEMON_PATH=`whereis onedrive-d | cut -d ' ' -f2 | cat -`

DAEMON_USER="$SUDO_USER"
if [ "${#DAEMON_USER}" -eq "0" ]; then
	DAEMON_USER="$USER"
fi

PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
	log_daemon_msg "Starting daemon $DAEMON_NAME"
	start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --startas $DAEMON_PATH
	log_end_msg $?
}

do_stop () {
	log_daemon_msg "Stopping daemon $DAEMON_NAME"
	start-stop-daemon --stop --pidfile $PIDFILE --retry 10 --signal INT
	log_end_msg $?
}

case "$1" in

	start|stop)
		do_${1}
		;;

	restart|reload|force-reload)
		do_stop
		do_start
		;;

	status)
		status_of_proc "$DAEMON_NAME" "$DAEMON_NAME" && exit 0 || exit $?
		;;
	
	*)
		echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
		exit 1
		;;
esac

exit 0

"""
	
	print "Installing the daemon script..."
	subp = subprocess.Popen(["cat - > /etc/init.d/onedrive-d && chmod u+x /etc/init.d/onedrive-d"], stdin=subprocess.PIPE, shell=True)
	subp.stdin.write(sh)
	ret = subp.communicate()
	subp.stdin.close()
	assert subp.returncode == 0
	print "Daemon script has been written to /etc/init.d/onedrive-d"
	
	print "Finished setting up the program."

def main():
	checkOSVersion()
	setupDaemon()
	print "All done."

if __name__ == "__main__":
	main()
