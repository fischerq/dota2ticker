#!/usr/bin/env python


import time
from threading import Lock

from websocket import WebsocketServer

from connectionserver import ConnectionServer
from gameserver import GameServer
from gameserver import GameDumper
from game import Game
from gameloader import ReplayLoader


connection_server = ConnectionServer("localhost", 29000)


GAME_ID = 303487989

game = Game()
loader = ReplayLoader(GAME_ID, game)

game_server_1 = GameServer("localhost", 29001)
connection_server.add_game_server(game_server_1)
game_server_1.set_loader(GAME_ID, loader)

dumper = GameDumper(GAME_ID)
dumper.select_loader(loader)

loader.load()