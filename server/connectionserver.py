#!/usr/bin/env python

from gevent import monkey; monkey.patch_all()
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication

# websocket import WebsocketServer
from threading import Thread
from threading import Lock
from utils import DataSocket

import protocols.connect as ConnectProtocol


class ConnectionApplication(WebSocketWSGIApplication):
    def __init__(self, server):
        super(ConnectionApplication, self).__init__(handler_cls=ConnectionSocket)
        self.server = server

    def make_websocket(self, sock, protocols, extensions, environ):
        websocket = self.handler_cls(sock, self.server)
        environ['ws4py.websocket'] = websocket
        return websocket


class ConnectionSocket(DataSocket):
    def __init__(self, sock, server):
        super(ConnectionSocket, self).__init__(sock=sock)
        self.connection_server = server

    def on_message(self, message):
        if not ConnectProtocol.check(message):
            print "Bad message"
            print message["Type"]
        elif message["Type"] == ConnectProtocol.Types.CONNECT:
            game_server = self.connection_server.find_game_server(message)
            if game_server is not None:
                client_message = self.connection_server.create_client()
            else:
                client_message = ConnectProtocol.RejectConnectionMessage()
            self.send_data(client_message)
        else:
            print "Not supported message: {}".format(message["Type"])
        self.close()


class ConnectionServer:
    def __init__(self, address, port):
        self.server = WSGIServer((address, port), ConnectionApplication(self))
        self.game_servers = []
        self.game_servers_lock = Lock()
        Thread(target=self.server.serve_forever).start()

    def add_game_server(self, game_server):
        with self.game_servers_lock:
            self.game_servers.append(game_server)

    def find_game_server(self, message):
        game_id = message["GameID"]
        server = None
        with self.game_servers_lock:
            for game_server in self.game_servers:
                if game_server.provides_game(game_id):
                    server = game_server
                    break
        return server