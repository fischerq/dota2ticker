#!/usr/bin/env python

from server.connectionserver.connectionserver import ConnectionServer
import server.config as config
import os
print "connect dir: {}".format(os.getcwd())
connection_server = ConnectionServer(config.host, config.public_port, config.public_address, config.internal_port)
print "Started Connectionserver"
connection_server.start()