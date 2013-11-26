#!/usr/bin/env python

from gevent import monkey; monkey.patch_all()
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from threading import Lock
from threading import Thread
from utils import DataSocket

import protocols.game as GameProtocol
import protocols.connect as ConnectProtocol


class GameApplication(WebSocketWSGIApplication):
    def __init__(self, server):
        super(GameApplication, self).__init__(handler_cls=GameSocket)
        self.server = server

    def make_websocket(self, sock, protocols, extensions, environ):
        websocket = self.handler_cls(sock, self.server)
        environ['ws4py.websocket'] = websocket
        return websocket


class GameSocket(DataSocket):
    def __init__(self, sock, server):
        super(GameSocket, self).__init__(sock=sock)
        self.server = server
        self.registered = False
        self.client = None

    def on_message(self, message):
        if not GameProtocol.check(message):
            print "Bad message"
            return
        response = None
        if not self.registered:
            if message["Type"] != GameProtocol.MessageTypes.REGISTER:
                response = GameProtocol.ErrorMessage("Bad registration message")
                print "Bad registration message"
            elif not self.server.provides_game(message["GameID"]):
                response = GameProtocol.ErrorMessage("Game not provided")
                print "Bad registration, game not provided"
            else:
                self.client = self.server.find_client(message["ClientID"])
                self.client.connection = self
                self.registered = True
                response = GameProtocol.ConfirmMessage()
        else:
            message_type = message["Type"]
            if message_type == GameProtocol.MessageTypes.CONFIGURE:
                pass
            elif message_type == GameProtocol.MessageTypes.GETSTATE:
                response = GameProtocol.StateMessage(self.server.get_state(message["Time"]))
            elif message_type == GameProtocol.MessageTypes.SUBSCRIBE:
                self.server.add_subscriber(self.client, message["Mode"], message["Time"])
                response = GameProtocol.StateMessage(self.server.get_state(message["Time"]))
            else:
                print "Unknown message type {}".format(message_type)
        self.send_data(response)


PAST_SEND_INTERVAL = 0.1 # in seconds
TIME_PER_TICK = 1.0/30
import time

class GameServer:
    def __init__(self, host, port):
        self.host = host
        self.clients = []
        self.clients_lock = Lock()
        self.game_id = 0
        self.game = None
        self.server = WSGIServer((host, port), GameApplication(self))
        Thread(target=self.server.serve_forever).start()
        self.subscribers = dict()
        self.subscribers["Current"] = []
        self.subscribers["Past"] = []
        self.subscribers["Event"] = []
        Thread(target=self.serve_past_subscribers).start()

    def serve_past_subscribers(self):
        while True:
            time_change = PAST_SEND_INTERVAL / TIME_PER_TICK
            for subscriber, iterator in self.subscribers["Past"]:
                if iterator.next is None:
                    continue
                while iterator.current.time + time_change > iterator.next.time:
                    subscriber.send_update(iterator.next)
                    iterator.advance()
            self.subscribers["Past"][:] = [(s, it) for s, it in self.subscribers["Past"] if not it.next is None]
            time.sleep(PAST_SEND_INTERVAL)

    def find_client(self, client_id):
        with self.clients_lock:
            for client in self.clients:
                if client.id == client_id:
                    return client
        print "Couldn't find client"
        return None

    def create_client(self):
        client = Client(GameProtocol.generate_id())
        with self.clients_lock:
            self.clients.append(client)
        return ConnectProtocol.ClientInfoMessage(self.host, self.port, client.id, self.game_id)
    
    def provides_game(self, game_id):
        return self.game_id == game_id

    def set_loader(self, id_, loader):
        self.game_id = id_
        self.game = loader.game
        loader.add_update_listener(self.register_update)
        loader.add_event_listener(self.register_event)

    def add_subscriber(self, client, mode, time):
        self.subscribers["Event"].append(client)
        if mode is GameProtocol.SubscribeModes.CURRENT:
            self.subscribers["Current"].append(client)
        elif mode is GameProtocol.SubscribeModes.PAST:
            self.subscribers["Past"].append(client, self.game.update_iterator(time))

    def register_update(self, update):
        for client in self.subscribers["Current"]:
            client.send_update(update)

    def register_event(self, event):
        for client in self.subscribers["Event"]:
            client.send_event(event)


class Client:
    def __init__(self, id_):
        self.id = id_
        self.connection = None
        self.subscribe_mode = None
        self.subscribe_interval = 10
        self.subscribe_threshold = 0
        self.last_time = 0
        self.buffered_update = None

    def send_update(self, update):
        if self.buffered_update is None:
            self.buffered_update = update
        else:
            self.buffered_update.merge(update)
        if self.buffered_update.time >= self.last_time + self.subscribe_interval:
            message = GameProtocol.UpdateMessage(self.buffered_update)
            self.connection.send(message)
            self.last_time = self.buffered_update.time
            self.buffered_update = None

    def send_event(self, event):
        message = GameProtocol.EventMessage(event)
        if event.importance > self.subscribe_threshold:
                self.connection.send(message)


import simplejson as json


class GameDumper:
    def __init__(self, id):
        self.file = open("data/dumps/{}.json".format(id), "w+")

    def select_loader(self, loader):
        loader.add_event_listener(self.dump_event)
        loader.add_update_listener(self.dump_update)
        loader.add_finish_listener(self.close)

    def dump_event(self, event):
        message = GameProtocol.EventMessage(event)
        self.dump_message(message)

    def dump_update(self, update):
        message = GameProtocol.UpdateMessage(update)
        self.dump_message(message)

    def dump_message(self, message):
        self.file.write("{}\n".format(json.dumps(message, separators=(',', ': '), indent=4)))

    def close(self):
        self.file.close()