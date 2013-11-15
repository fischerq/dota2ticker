#!/usr/bin/env python


import time
from threading import Lock

from websocket import WebsocketServer

from connectionserver import ConnectionServer
from gameserver import GameServer
from gameserver import GameDumper
from game import Game
from gameloader import ReplayLoader


connection_server = ConnectionServer()


GAME_ID = 303487989

game = Game()
loader = ReplayLoader(GAME_ID, game)

game_server_1 = GameServer("localhost", 29001, 29002)
connection_server.add_game_server(game_server_1)
game_server_1.select_loader(GAME_ID, loader)

dumper = GameDumper(GAME_ID)
dumper.select_loader(loader)

loader.load()