#!/bin/bash

###############################################
# To use: 
# chmod +x install-redis.sh
# ./install-redis.sh
###############################################

version=5.0.0

echo "*****************************************"
echo " 1. Prerequisites: Install updates, install GCC, make, jemalloc, tcl"
echo "*****************************************"

sudo yum -y update
sudo yum -y install gcc gcc-c++ make jemalloc tcl

echo "*****************************************"
echo " 2. Download, Untar and Make Redis ${version}"
echo "*****************************************"

cd /usr/local/src
sudo wget "http://download.redis.io/releases/redis-${version}.tar.gz"
sudo rm -fr "redis-${version}"
sudo tar vxzf "redis-${version}.tar.gz"
sudo rm -f "redis-${version}.tar.gz"
cd "redis-${version}"
sudo make distclean
sudo make
sudo make test

echo "*****************************************"
echo " 3. Create Directories and Copy Redis Files"
echo "*****************************************"

sudo mkdir /etc/redis /var/lib/redis
sudo cp -f src/redis-server src/redis-cli /usr/local/bin

echo "*****************************************"
echo " 4. Configure Redis.Conf"
echo "*****************************************"
echo " Edit redis.conf as follows:"
echo " 1: ... daemonize yes"
echo " 2: ... bind 127.0.0.1"
echo " 3: ... dir /var/lib/redis"
echo " 4: ... loglevel notice"
echo " 5: ... logfile /var/log/redis.log"
echo "*****************************************"

sudo sed -e "s/^daemonize no$/daemonize yes/" -e "s/^# bind 127.0.0.1$/bind 127.0.0.1/" -e "s/^dir \.\//dir \/var\/lib\/redis\//" -e "s/^loglevel verbose$/loglevel notice/" -e "s/^logfile \"\"$/logfile \/var\/log\/redis.log/" redis.conf | sudo tee /etc/redis/redis.conf

echo "*****************************************"
echo " 5. Download init Script"
echo "*****************************************"

sudo wget https://raw.github.com/saxenap/install-redis-amazon-linux-centos/master/redis-server

echo "*****************************************"
echo " 6. Move and Configure Redis-Server"
echo "*****************************************"

sudo mv -f redis-server /etc/init.d
sudo chmod 755 /etc/init.d/redis-server

echo "*****************************************"
echo " 7. Auto-Enable Redis-Server"
echo "*****************************************"

sudo chkconfig --add redis-server
sudo chkconfig --level 345 redis-server on

echo "*****************************************"
echo " 8. Start Redis Server"
echo "*****************************************"

sudo service redis-server start

echo "*****************************************"
echo " Complete!"
echo " You can test your redis installation using the redis console:"
echo "   $ redis-cli"
echo "   127.0.0.1:6379> set foo bar"
echo "   OK"
echo "   127.0.0.1:6379> get foo"
echo "   \"bar\""
echo "*****************************************"
read -p "Press [Enter] to continue..."
