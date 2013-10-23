#!/usr/bin/env python


import time
from threading import Lock

from websocket import WebsocketServer

from connectionserver import ConnectionServer
from gameserver import GameServer

connection_server = ConnectionServer()

game_server_1 = GameServer("localhost", 29001, 29002)
connection_server.addGameServer(game_server_1)
