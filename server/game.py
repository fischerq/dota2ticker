#!/usr/bin/env python
import copy

class Game:
    def __init__(self, id_):
        self.id = id_
        self.snapshots = []
        self.updates = []
        self.messages = []
        self.listener_update = None;
        self.listener_message = None;
    def getState(self, time):
        #TODO
        state = dict()
        state["Time"] = time
        state["GameID"] = self.id
        return state
    def getUpdates(self, start, end):
        pass
    def initialise(self, state):
        pass
    def addUpdate(self, time, changes):
        self.updates.append((time, changes))
        self.listener_update((time, changes))

    def addMessage(self, message):
        self.messages.append(message)
        self.listener_update(message)

    def setUpdateListener(self, listener):
        self.listener_update = listener

    def setMessageListener(self, listener):
        self.listener_message = listener

class Change:
    def __init__(self):
        self.property = [] #list of nested identifiers
        self.value = None #new value
    def apply(self, change):
        pass

class Update:
    def __init__(self, origin, time, changes = []):
        self.origin = origin
        self.time = time
        self.changes = copy.deepcopy(changes)
    @staticmethod
    def merge(update1, update2):
        if update1.time > update2.time:
            return Update.merge(update2, update1)
        if update2.origin < update1.time:
            print "Merging Bad Updates"
        new_update = Update(update2.time, update1.changes)
        for change in update2.changes:
            if False: #same property changed
                pass #add changes
        return new_update