dota2ticker
===========


Install-guide:

apt-get install python
apt-get install git

Instally nginx
set paths in /etc/init.d/nginx

clone repo


apt-get install python-dev python-snappy python-protobuf

easy_install gevent
easy_install simplejson

install protobuf 2.5:
    wget http://protobuf.googlecode.com/files/protobuf-2.5.0.tar.gz
    tar -xzvf file.tar.gz
    cd protobuf-2.5.0
	./configure
    make
    make check
    make install

in /python:
change /etc/ld.so.conf: 
add line 
    /usr/local/lib

run 
    ldconfig

    export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp
    python setup.py build
    python setup.py test
    python setup.py install

	
cp dota2ticker /etc/init.d

start daemon with /etc/init.d/dota2ticker start

add permissions for daemon:
    chown -R dota2ticker dota2ticker
install flask:
	easy_install flask