#!/usr/bin/env python

from websocket import WebsocketServer
from threading import Lock
from utils import DataConnection

import protocol as Protocol
from protocol import MessageType
import gameserver

class ConnectionServer(WebsocketServer):
    def __init__(self):
        WebsocketServer.__init__(self, 29000, self.handleClient)
        self.game_servers = []
        self.game_servers_lock = Lock()
        self.start()
    def addGameServer(self, game_server):
        with self.game_servers_lock:
            self.game_servers.append(game_server)
        
    def handleClient(self, client):
        connection = DataConnection(client)
        connect_message = connection.receive()
        if (not Protocol.check(connect_message)) or (connect_message["Type"] != MessageType.CONNECT):
            print "Bad connection message"
            print Protocol.check(connect_message)
            print connect_message["Type"]
        else:
            server = self.findGameServer(connect_message)
            if server is not None:
                client_message = server.createClient()
            else:
                client_message = ConnectionServer.rejectConnection()
            connection.send(client_message)
        connection.close()
    @staticmethod
    def rejectConnection():
        message = dict()
        message["Type"] = MessageType.REJECT_CONNECTION
        return message
    def findGameServer(self, message):
        game_id = message["GameID"]
        server = None
        with self.game_servers_lock:
            for game_server in self.game_servers:
                if game_server.providesGame(game_id):
                    server = game_server
                    break
        return server
            
                    
        
