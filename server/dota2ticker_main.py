#!/usr/bin/env python


import time
from threading import Lock

from websocket import WebsocketServer

from connectionserver import ConnectionServer
from gameserver import GameServer
from gameserver import GameDumper
from game import Game
from gameloader import GameLoader


connection_server = ConnectionServer()

game_server_1 = GameServer("localhost", 29001, 29002)
connection_server.add_game_server(game_server_1)

GAME_ID = 303487989

game = Game()
game_server_1.select_game(GAME_ID, game)

dumper = GameDumper(GAME_ID)
dumper.select_game(game)

loader = GameLoader(GAME_ID, game)
loader.load()