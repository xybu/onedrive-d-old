echo "Checking if package \"python-pip\" is installed..."
dpkg-query -l python-pip
if [ $? -eq 1 ]; then
	echo "Installing package python-pip..."
	sudo apt-get -y install python-pip
fi

echo "Checking if package \"libyaml\" is installed..."
dpkg-query -l libyaml-dev
if [ $? -eq 1 ]; then
	echo "Installing package libyaml-dev..."
	sudo apt-get -y install libyaml-dev
fi

# Note that to install stuff in system-wide PATH and site-packages, 
# elevated privileges are often required.
# Use "install --user", ~/.pydistutils.cfg or
# virtualenv to do unprivileged installs into custom paths.
echo "Installing python-skydrive..."
sudo pip install 'git+https://github.com/mk-fg/python-skydrive.git#egg=python-skydrive[standalone]'

echo "Installing PyYAML..."
#cd ~ && 
wget -O - "http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz" | tar xzf -
cd PyYAML-3.10 && sudo python2 setup.py --with-libyaml install
cd ..

echo "Cleaning..."
rm -rfv PyYAML-3.10
