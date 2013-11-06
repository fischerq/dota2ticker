#!/usr/bin/env python

from websocket import WebsocketServer
from threading import Lock
from utils import DataConnection

import protocol
from protocol import MessageType


class ConnectionServer(WebsocketServer):
    def __init__(self):
        WebsocketServer.__init__(self, 29000, self.handle_client)
        self.game_servers = []
        self.game_servers_lock = Lock()
        self.start()

    def add_game_server(self, game_server):
        with self.game_servers_lock:
            self.game_servers.append(game_server)
        
    def handle_client(self, client):
        connection = DataConnection(client)
        connect_message = connection.receive()
        if (not protocol.check(connect_message)) or (connect_message["Type"] != MessageType.CONNECT):
            print "Bad connection message"
            print protocol.check(connect_message)
            print connect_message["Type"]
        else:
            server = self.find_game_server(connect_message)
            if server is not None:
                client_message = server.create_client()
            else:
                client_message = ConnectionServer.reject_connection()
            connection.send(client_message)
        connection.close()
    @staticmethod
    def reject_connection():
        message = dict()
        message["Type"] = MessageType.REJECT_CONNECTION
        return message

    def find_game_server(self, message):
        game_id = message["GameID"]
        server = None
        with self.game_servers_lock:
            for game_server in self.game_servers:
                if game_server.provides_game(game_id):
                    server = game_server
                    break
        return server