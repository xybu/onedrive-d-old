install_pkg() {
	echo "Checking if package \"$1\" is installed..."
	dpkg-query -l $1 > tmp.txt
	if [ $? -eq 1 ]; then
		echo "Installing package $1..."
		sudo apt-get -y install $1
	else
		echo "Package $1 is installed. Skip this step."
	fi
	rm tmp.txt
}

install_pkg python-pip
install_pkg libyaml-dev
install_pkg python-yaml

# Note that to install stuff in system-wide PATH and site-packages, 
# elevated privileges are often required.
# Use "install --user", ~/.pydistutils.cfg or
# virtualenv to do unprivileged installs into custom paths.
echo "Installing/Upgrading python-skydrive..."
sudo pip install 'git+https://github.com/mk-fg/python-skydrive.git#egg=python-skydrive[standalone]' --upgrade
