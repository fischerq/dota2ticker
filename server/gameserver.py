#!/usr/bin/env python

import protocol as Protocol
from protocol import MessageType
from threading import Lock
from utils import DataConnection
from websocket import WebsocketServer

from game import Game

class GameServer:
    def __init__(self, host, port_requests, port_listeners):
        self.host = host
        self.clients = []
        self.clients_lock = Lock()
        self.game_id = 0
        self.game = None
        self.request_server = WebsocketServer(port_requests, self.handleRequestClient)
        self.request_server.start()
        self.listener_server = WebsocketServer(port_listeners, self.handleListenerClient)
        self.listener_server.start()
        
    def handleRequestClient(self, client):
        connection = DataConnection(client)
        register_message = connection.receive()
        if not Protocol.check(register_message) or register_message["Type"] != MessageType.REGISTER:
            print "Bad registration message"
            return
        if not self.providesGame(register_message["GameID"]):
            print "Bad registration, game not provided"
            return
        client = self.findClient(register_message["ClientID"])
        client.request = connection
        run = True
        while run:
            request = connection.receive()
            if not Protocol.check(request):
                print "Bad request"
                continue
            run = self.processRequest(client, request)     
        
    def handleListenerClient(self, client):
        connection = DataConnection(client)
        register_message = connection.receive()
        if not Protocol.check(register_message) or register_message["Type"] != MessageType.REGISTER:
            print "Bad registration message"
            return
        if not self.providesGame(register_message["GameID"]):
            print "Bad registration, game not provided"
            return
        client = self.findClient(register_message["ClientID"])
        client.listener = connection
        
    def findClient(self, client_id):
        with self.clients_lock:
            for client in self.clients:
                if client.id == client_id:
                    return client
        print "Couldn't find client"
        return None

    
    def createClient(self):
        client = Client(Protocol.generateID())
        with self.clients_lock:
            self.clients.append(client)
        message = dict()
        message["Type"] = MessageType.CLIENT_INFO 
        message["PortRequest"] = self.request_server.port
        message["PortListener"] = self.listener_server.port
        message["Host"] = self.host
        message["ClientID"] = client.id
        message["GameID"] = self.game_id
        return message
    
    def providesGame(self, game_id):
        return self.game_id == game_id

    def processRequest(self, client, request):
        answer = dict()
        request_type = request["Type"]
        if request_type == MessageType.CONFIGURE:
            pass
        elif request_type == MessageType.GETSTATE:
            answer["Type"] = MessageType.STATE
            answer["State"] = self.game.getState(request["Time"])
            client.request.send(answer)
        elif request_type == MessageType.SUBSCRIBE:
            pass
        else:
            print "unknown message type {}".format(request_type)
        return True
    
    def loadGame(self, id_):
        self.game_id = id_
        self.game = Game(id_)
        self.game.setUpdateListener(self.registerUpdate)
        self.game.setMessageListener(self.registerMessage)

    def registerUpdate(self):
        pass
class Client:
    def __init__(self, id_):
        self.id = id_
        self.listener = None
        self.request = None
        self.subscribe_mode = None
        self.subscribe_interval = None
        self.current_time = 0