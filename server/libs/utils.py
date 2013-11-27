#!/usr/bin/env python


def enum(*sequential):
    enums = dict()
    for i, x in enumerate(sequential):
        enums[x] = x
    return type('Enum', (), enums)

import simplejson as json
from ws4py.websocket import WebSocket

class DataSocket(WebSocket):
    def opened(self):
        pass

    def received_message(self, message):
        if not message.is_text:
            print "DataSocket received binary data - expecting only text"
            return
        else:
            self.on_message(json.loads(message.data))

    def send_data(self, data):
        self.send(json.dumps(data), False)

    def closed(self, code, reason=None):
        pass