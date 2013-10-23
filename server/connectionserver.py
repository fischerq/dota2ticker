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
        self.gameservers = []
        self.gameservers_lock = Lock()
        self.start()
    def addGameServer(self, game_server):
        with self.gameservers_lock:
            self.gameservers.append(game_server)
        
    def handleClient(self, client):
        connection = DataConnection(client)
        connect_message = connection.recieve()
        if not Protocol.check(connect_message) or connect_message["Type"] != MessageType.CONNECT:
            print "Bad connection message"
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
        with self.gameservers_lock:
            for gameserver in self.gameservers:
                if gameserver.providesGame(game_id):
                    server = gameserver
                    break
        return server
            
                    
        
