#!/usr/bin/env python

from threading import Thread
from game import *
import time
import tarrasque
import skadi

class GameLoader:
    def __init__(self, game_id, game):
        self.game = game
        self.game_id = game_id
        pass

    def load(self):
        Thread(target=self.load_game).start()

    def load_game(self):
        state = State(0)
        self.game.initialise(state)

        #file_replay = "data/replays/{}.dem".format(self.game_id)
        #replay = tarrasque.StreamBinding.from_file(file_replay)

        message = dict()
        message["Type"] = "Start"
        message["Importance"] = 2
        self.game.add_event(message)
        for i in range(1, 600):
            update = Update(i-1, i)
            update.add_change(Change(["World","Time"], i))
            self.game.add_update(update)
            if i % 10 ==0:
                message = dict()
                message["Time"] = i
                message["Type"] = "10er"
                message["Importance"] = 2
                self.game.add_event(message)
            elif i % 5 == 0:
                message = dict()
                message["Time"] = i
                message["Type"] = "5er"
                message["Importance"] = 1
                self.game.add_event(message)
            elif i % 2 == 0:
                message = dict()
                message["Time"] = i
                message["Type"] = "2er"
                message["Importance"] = 1
                self.game.add_event(message)
            time.sleep(1)