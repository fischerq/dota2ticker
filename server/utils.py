#!/usr/bin/env python


def enum(*sequential):
    enums = dict()
    for i, x in enumerate(sequential):
        enums[x] = x
    return type('Enum', (), enums)

import simplejson as json
import websocket
from websocket import WebsocketConnection


class DataConnection:
    def __init__(self, websocket_connection):
        self.connection = websocket_connection
        self.connected = True

    def send(self, data):
        message = json.dumps(data)
        self.connection.send(message)

    def receive(self):
        (operation, message) = self.connection.receive()
        if operation is websocket.OP_CLOSE:
            self.connection.close()
            self.connected = False
            print "Remote closed"
            return None
        elif operation is not websocket.OP_TEXT:
            print "DataConnection: received bad message {}".format(operation)
            return None
        print "{}: received {}".format(self.connection.port, message)
        return json.loads(message)

    def close(self):
        self.connection.close()
        print "DataConnection: closed"
        self.connected = False
