#!/usr/bin/env python

from server.connectionserver.connectionserver import ConnectionServer


connection_server = ConnectionServer("localhost", 29000, 30000)
connection_server.start()