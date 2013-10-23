#!/usr/bin/env python

def enum(*sequential):
    enums = dict()
    for i, x in enumerate(sequential):
        enums[x] = i
    return type('Enum', (), enums)

import simplejson as json
import websocket
from websocket import WebsocketConnection

class DataConnection:
    def __init__(self, websocket_connection):
        self.connection = websocket_connection
    def send(self, data):
        message = json.dumps(data)
        self.connection.send(message)
    def recieve(self):
        (operation, message) = self.connection.recieve()
        if operation is not websocket.OP_TEXT:
            print "DataConnection: recieved bad message"
            message = ""
        return json.loads(message)
    def close(self):
        (operation, message) = self.connection.recieve()
        if operation is not websocket.OP_CLOSE:
            print "DataConnection: tried to close, recieved data"
        else:
            self.connection.close()
