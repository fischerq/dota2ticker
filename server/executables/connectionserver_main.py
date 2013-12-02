#!/usr/bin/env python

from server.connectionserver.connectionserver import ConnectionServer

connection_server = ConnectionServer("0.0.0.0", 29000, 30000)
print "Started Connectionserver"
connection_server.start()