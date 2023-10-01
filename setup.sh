#! /bin/sh

# Pass username to this script as first argument
# sudo sh setup.sh soroosh

# Install Python pip and virtualenv
apt-get update

apt-get install python3-venv python3-dev python3-pip
pip install virtualenv
virtualenv cenv

# Switch to virtualenv and install required packages
. ./cenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Add specified user to sudoers file so that file operations using sudo do not require providing a password
echo "$1 ALL=(ALL) NOPASSWD: /usr/bin/mkdir , /usr/bin/mv , /usr/bin/cp , /usr/bin/rm" | (EDITOR="tee -a" visudo)

# Install and configure redis
apt-get install redis

# Install and configure openresty
apt-get -y install --no-install-recommends wget gnupg ca-certificates

# For ubuntu 16-20
# wget -O - https://openresty.org/package/pubkey.gpg | sudo apt-key add -

# For ubuntu 22
wget -O - https://openresty.org/package/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/openresty.gpg

# For ubuntu 16-20
#echo "deb http://openresty.org/package/ubuntu $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/openresty.list

# For ubuntu 22
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/openresty.gpg] http://openresty.org/package/ubuntu $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/openresty.list > /dev/null

apt-get update
apt-get -y install openresty

# Check openresty status
systemctl status openresty

# Install lua5.3
apt-get install lua5.3

# Update settings
echo "Update ALLOWED_HOSTS in $PWD/ccache/ccache/settings.py with server ip. Remember to include localhost as well."

echo "[Unit]\nDescription=gunicorn socket\n\n[Socket]\nListenStream=/run/gunicorn.sock\n\n[Install]\nWantedBy=sockets.target" > /etc/systemd/system/gunicorn.socket

echo "[Unit]\nDescription=gunicorn daemon\nRequires=gunicorn.socket\nAfter=network.target\n\n[Service]\nUser=$1\nGroup=www-data\nWorkingDirectory=$PWD/ccache\nExecStart=$PWD/cenv/bin/gunicorn  --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock ccache.wsgi:application\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/gunicorn.service

systemctl start gunicorn.socket
systemctl enable gunicorn.socket

mkdir logs
mkdir ccache/tmp

touch ./logs/uploads.log
chown nobody:nogroup ./logs/uploads.log

cd ccache
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata users.json

systemctl restart gunicorn
