#!/bin/sh
PYTHONPATH=$PYTHONPATH:/usr/local/dota2ticker
python server/executables/connectionserver_main.py > connection_server.log
