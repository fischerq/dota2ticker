#!/usr/bin/env python

from gevent import monkey; monkey.patch_all()
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from threading import Thread
from server.libs.utils import DataSocket
import socket


from server.protocols import game as GameProtocol
from server import protocols as Protocols

from server.libs.game import Game


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
                self.client = self.server.create_client()
                self.client.connection = self
                self.registered = True
                response = GameProtocol.ConfirmMessage()
        else:
            message_type = message["Type"]
            print message
            if message_type == GameProtocol.MessageTypes.CONFIGURE:
                pass
            elif message_type == GameProtocol.MessageTypes.GETSTATE:
                response = GameProtocol.StateMessage(self.server.game, int(message["Time"]))
            elif message_type == GameProtocol.MessageTypes.SUBSCRIBE:
                current_time = int(message["Time"])
                mode = message["Mode"]
                if message["Mode"] == GameProtocol.SubscribeModes.CURRENT:
                    if not self.server.game.complete:
                        current_time = self.server.game.current_state.time
                    else:
                        current_time = self.server.game.current_state.get(0, "pregame_start_time")
                        mode = GameProtocol.SubscribeModes.PAST
                self.server.add_subscriber(self.client, mode, current_time)
                print "sending state for time {}".format(current_time)
                print self.server.game.get_state(current_time).data
                response = GameProtocol.StateMessage(self.server.game, current_time)
            elif message_type == GameProtocol.MessageTypes.UNSUBSCRIBE:
                print "Unsubscribing"
                self.server.remove_subscriber(self.client)
            else:
                print "Unknown message type {}".format(message_type)
        try:
            self.send_data(response)
        except socket.error as e:
            print "Error sending response: {}".format(e)
            self.close()

    def closed(self, code, reason=None):
        self.server.remove_client(self.client)

PAST_SEND_INTERVAL = 5  # in ticks
TIME_PER_TICK = 1.0/30
TIMEOUT_INTERVAL = 5  # in seconds
SERVICE_TIMEOUT = 10  # in seconds
import time


class GameServer:
    def __init__(self, host, port, public_address,  game_id):
        self.host = host
        self.port = port
        self.public_address = public_address
        self.clients = []
        self.game_id = game_id
        self.game = Game()
        self.server = WSGIServer((host, port), GameApplication(self))
        self.subscribers = dict()
        self.subscribers["Current"] = []
        self.subscribers["Past"] = []
        self.subscribers["Event"] = []
        self.running = True
        self.webserver_thread = Thread(target=self.server.serve_forever, args=(0.5,))
        self.past_subscribers_thread = Thread(target=self.serve_past_subscribers)
        self.timeout_thread = Thread(target=self.timeout)

    def start(self):
        self.webserver_thread.start()
        self.past_subscribers_thread.start()
        self.timeout_thread.start()
        print "Started game server on {}, {}".format(self.host, self.port)

    def serve_past_subscribers(self):
        while self.running:
            for subscriber, past_state in self.subscribers["Past"]:
                if past_state.finished():
                    continue
                updates, events = past_state.pass_time(PAST_SEND_INTERVAL*subscriber.speed)
                for update in updates:
                    subscriber.send_update(update)
                for event in events:
                    subscriber.send_event(event)

            self.subscribers["Past"][:] = [(s, ps) for s, ps in self.subscribers["Past"] if not ps.finished()]
            time.sleep(PAST_SEND_INTERVAL * TIME_PER_TICK)

    def timeout(self):
        timeout = SERVICE_TIMEOUT
        while self.running:
            time.sleep(TIMEOUT_INTERVAL)
            print "Checking Timeout"
            total_subscribers = len(self.subscribers["Current"])+len(self.subscribers["Past"])+len(self.subscribers["Event"])
            if total_subscribers > 0 or not self.game.complete:
                timeout = SERVICE_TIMEOUT
            else:
                timeout -= TIMEOUT_INTERVAL
            print "{}".format(timeout)
            if timeout < 0:
                print "Timeout: shutting down gameserver"
                self.running = False
                self.server.stop()
        print "Finished timeout-thread"

    def find_client(self, client_id):
        for client in self.clients:
            if client.id == client_id:
                return client
        print "Couldn't find client"
        return None

    def create_client(self):
        client = Client(Protocols.generate_id())
        self.clients.append(client)
        return client

    def remove_client(self, client):
        self.remove_subscriber(client)
        self.clients[:] = [c for c in self.clients if c.id != client.id]
    
    def provides_game(self, game_id):
        return self.game_id == game_id

    def add_subscriber(self, client, mode, time):
        if mode == GameProtocol.SubscribeModes.CURRENT:
            self.subscribers["Event"].append(client)
            self.subscribers["Current"].append(client)
        elif mode == GameProtocol.SubscribeModes.PAST:
            client.set_time(time)
            self.subscribers["Past"].append((client, self.game.past_state(time)))

    def remove_subscriber(self, client):
        self.subscribers["Event"][:] = [c for c in self.subscribers["Event"] if c.id != client.id]
        self.subscribers["Current"][:] = [(s, it) for s, it in self.subscribers["Past"] if s.id != client.id]
        self.subscribers["Past"][:] = [(s, it) for s, it in self.subscribers["Past"] if s.id != client.id]

    def register_update(self, update):
        self.game.add_update(update)
        for client in self.subscribers["Current"]:
            client.send_update(update)

    def register_event(self, event):
        self.game.add_event(event)
        for client in self.subscribers["Event"]:
            client.send_event(event)

    def finish(self):
        self.game.finish()


class Client:
    def __init__(self, id_):
        self.id = id_
        self.connection = None
        self.subscribe_mode = None
        self.subscribe_interval = 10
        self.subscribe_threshold = 0
        self.last_time = 0
        self.buffered_update = None
        self.speed = 2

    def set_time(self, time):
        self.buffered_update = None
        self.last_time = time

    def send_update(self, update):
        if self.buffered_update is None:
            self.buffered_update = update
        else:
            self.buffered_update.merge(update)
        if self.buffered_update.time >= self.last_time + self.subscribe_interval:
            message = GameProtocol.UpdateMessage(self.buffered_update)
            try:
                self.connection.send_data(message)
            except socket.error as e:
                print "Failed sending update to client: {}".format(e)
                self.connection.close()
            self.last_time = self.buffered_update.time
            self.buffered_update = None

    def send_event(self, event):
        message = GameProtocol.EventMessage(event)
        if event.importance > self.subscribe_threshold:
            try:
                self.connection.send_data(message)
            except socket.error as e:
                print "Failed sending event to client: {}".format(e)
                self.connection.close()