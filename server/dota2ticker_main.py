#!/usr/bin/env python


import time
from threading import Lock

from websocket import WebsocketServer

from connectionserver import ConnectionServer
from gameserver import GameServer

connection_server = ConnectionServer()

game_server_1 = GameServer("localhost", 29001, 29002)
connection_server.add_game_server(game_server_1)
game_server_1.load_game(303487989)