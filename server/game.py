#!/usr/bin/env python

class Game:
    def __init__(self, id_):
        self.id = id_
    def getState(self, time):
        state = dict()
        state["Time"] = time
        state["GameID"] = self.id
        return state
