#!/usr/bin/env python

import protocol as Protocol
from protocol import MessageType
from threading import Lock
from utils import DataConnection
from websocket import WebsocketServer

from game import Game
from gameloader import GameLoader

from events import Event
import simplejson as json


class GameServer:
    def __init__(self, host, port_requests, port_listeners):
        self.host = host
        self.clients = []
        self.clients_lock = Lock()
        self.game_id = 0
        self.game = None
        self.request_server = WebsocketServer(port_requests, self.handle_request_client)
        self.request_server.start()
        self.listener_server = WebsocketServer(port_listeners, self.handle_listener_client)
        self.listener_server.start()
        self.immediate_subscribers = []
        self.interval_subscribers = []
        self.event_subscribers = []
        self.dump_file = open("data/dumps/{}.json".format(self.game_id), "w+")

    def handle_request_client(self, client):
        connection = DataConnection(client)
        register_message = connection.receive()
        if not Protocol.check(register_message) or register_message["Type"] != MessageType.REGISTER:
            print "Bad registration message"
            return
        if not self.provides_game(register_message["GameID"]):
            print "Bad registration, game not provided"
            return
        client = self.find_client(register_message["ClientID"])
        client.request = connection
        confirm_message = dict()
        confirm_message["Type"] = MessageType.CONFIRM
        client.request.send(confirm_message)
        run = True
        while run:
            request = connection.receive()
            if not Protocol.check(request):
                print "Bad request"
                continue
            if not connection.connected:
                break;
            run = self.process_request(client, request)
        
    def handle_listener_client(self, client):
        connection = DataConnection(client)
        register_message = connection.receive()
        if not Protocol.check(register_message) or register_message["Type"] != MessageType.REGISTER:
            print "Bad registration message"
            return
        if not self.provides_game(register_message["GameID"]):
            print "Bad registration, game not provided"
            return
        client = self.find_client(register_message["ClientID"])
        client.listener = connection
        confirm_message = dict()
        confirm_message["Type"] = MessageType.CONFIRM
        client.listener.send(confirm_message)

    def find_client(self, client_id):
        with self.clients_lock:
            for client in self.clients:
                if client.id == client_id:
                    return client
        print "Couldn't find client"
        return None

    def create_client(self):
        client = Client(Protocol.generate_id())
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
    
    def provides_game(self, game_id):
        return self.game_id == game_id

    def process_request(self, client, request):
        answer = dict()
        request_type = request["Type"]
        if request_type == MessageType.CONFIGURE:
            pass
        elif request_type == MessageType.GETSTATE:
            answer["Type"] = MessageType.STATE
            answer["State"] = self.game.get_state(request["Time"])
            client.request.send(answer)
        elif request_type == MessageType.SUBSCRIBE:
            self.immediate_subscribers.append(client)
            self.event_subscribers.append(client)
            message = dict()
            message["Type"] = MessageType.STATE
            message["State"] = self.game.get_state(self.game.latest_update).get_data()
            client.listener.send(message)
        else:
            print "unknown message type {}".format(request_type)
        return True
    
    def load_game(self, id_):
        self.game_id = id_
        self.game = Game(id_)
        self.game.set_update_listener(self.register_update)
        self.game.set_event_listener(self.register_event)
        game_loader = GameLoader(self.game_id, self.game)
        game_loader.load()

    def register_update(self, update):
        message = Protocol.UpdateMessage(update)
        for client in self.immediate_subscribers:
            client.listener.send(message)
        self.dump_message(message)

    def register_event(self, event):
        message = Protocol.EventMessage(event)
        for client in self.event_subscribers:
            if event.importance > client.subscribe_threshold:
                client.listener.send(message)
        self.dump_message(message)

    def dump_message(self, message):
        self.dump_file.write("{}\n".format(json.dumps(message)))


class Client:
    def __init__(self, id_):
        self.id = id_
        self.listener = None
        self.request = None
        self.subscribe_mode = None
        self.subscribe_interval = None
        self.subscribe_threshold = 0
        self.current_time = 0