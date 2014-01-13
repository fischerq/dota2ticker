#!/usr/bin/env python

from gevent import monkey; monkey.patch_all()
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from gevent.server import StreamServer

from server.libs.utils import DataSocket
from server.protocols import connect as ConnectProtocol

import subprocess
import socket
import os.path

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
        elif message["Type"] == ConnectProtocol.MessageTypes.CONNECT:
            print "Received connect message"
            availability, game_server = self.connection_server.find_game_server(message)
            try:
                self.send_data(ConnectProtocol.GameAvailabilityMessage(availability))
                if availability is ConnectProtocol.AvailabilityStates.AVAILABLE:
                    self.send_data(ConnectProtocol.ClientInfoMessage(game_server["host"], game_server["port"], game_server["game_id"]))
            except socket.error as e:
                print "Error sending connect response: {}".format(e)
        else:
            print "Not supported message: {}".format(message["Type"])
        self.close()


class ConnectionServer:
    def __init__(self, host, port, public_address, registration_port):
        self.server = WSGIServer((host, port), ConnectionApplication(self))
        self.public_address = public_address
        self.game_servers = []
        self.next_gs_port = port + 1
        self.next_loader_port = registration_port + 1
        self.loaders = []
        self.requested_games = []
        self.registration_port = registration_port
        self.registration_server = StreamServer((host, self.registration_port), self.handle_registration)
        self.registration_server.start()

    def find_game_server(self, message):
        game_id = int(message["GameID"])
        server = None
        for game_server in self.game_servers:
            if game_server["game_id"] == game_id:
                return ConnectProtocol.AvailabilityStates.AVAILABLE, game_server
        if server is None:
            response = ConnectProtocol.AvailabilityStates.PENDING, None
            if game_id in self.requested_games:
                print "server to be created is already requested"
            else:
                if os.path.isfile("server/data/replays/{}.dem".format(game_id)):
                    self.create_game_server(game_id)
                else:
                    response = ConnectProtocol.AvailabilityStates.UNAVAILABLE, None
            return response

    def handle_registration(self, socket_, address):
        message = socket_.recv(1024)
        data = message.split(" ")
        if data[0] == "GAME_SERVER" and len(data) is 4:
            server = dict()
            server["host"] = data[1]
            server["port"] = int(data[2])
            server["game_id"] = int(data[3])
            print "registered game server for game {} at ({},{})".format(server["game_id"], server["host"], server["port"])
            self.game_servers.append(server)
            self.requested_games.remove(server["game_id"])
            socket_.sendall("ACCEPTED")
        elif data[0] == "REMOVE_GAME_SERVER" and len(data) is 2:
            print "removed game server at host"
            self.game_servers[:] = [s for s in self.game_servers if s["game_id"] != int(data[1])]
            socket_.sendall("ACCEPTED")
        elif data[0] == "LOADER" and len(data) is 3:
            loader = dict()
            loader["game_id"] = int(data[1])
            loader["port"] = int(data[2])
            print "registered loader for game {} at port {}".format(loader["game_id"], loader["port"])
            self.loaders.append(loader)
            socket_.sendall("ACCEPTED")
            if loader["game_id"] in self.requested_games:
                 self.create_game_server(loader["game_id"])
        elif data[0] == "REMOVE_LOADER" and len(data) is 2:
            print "removed loader at host"
            self.loaders[:] = [l for l in self.loaders if l["game_id"] != int(data[1])]
            socket_.sendall("ACCEPTED")
        else:
            socket_.sendall("ERROR")
            print "Bad message: {} parsed: {}".format(message, data)
            print "{}, {}, {}".format(data[0] == "GAME_SERVER", data[0] == "LOADER", len(data))
        socket_.close()

    def create_game_server(self, game_id):
        print "Trying to create server for game {}".format(game_id)
        loader_port = -1
        for loader in self.loaders:
            if loader["game_id"] == game_id:
                loader_port = loader["port"]
                break
        if loader_port < 0:
            print "Spawning Loader"
            loader_port = self.next_loader_port
            subprocess.Popen(["python", "server/executables/loader_main.py", str(game_id), str(loader_port), str(self.registration_port)])
            self.next_loader_port += 1
            self.requested_games.append(game_id)
        else:
            print "Creating server for game {} that registers at {}".format(game_id, self.registration_port)
            subprocess.Popen(["python", "server/executables/gameserver_main.py", str(game_id),  str(self.next_gs_port), str(self.registration_port), self.public_address, str(loader_port)])
            self.next_gs_port += 1

    def start(self):
        self.server.serve_forever()




