#!/usr/bin/env python
from database import State, Update

SNAPSHOT_INTERVAL = 1000


class Game:
    def __init__(self):
        self.listeners_update = []
        self.listeners_event = []

        self.current_state = State(0)
        self.snapshots = []
        self.snapshots.append(self.current_state)
        self.updates = []
        self.events = []
        self.complete = False
        self.next_object_id = 0

    def initialise(self):
        self.current_state = State(0)
        self.snapshots = []
        self.snapshots.append(self.current_state)
        self.updates = []
        self.events = []
        self.complete = False
        self.next_object_id = 0

    def get_object_id(self):
        next_id = self.next_object_id
        self.next_object_id += 1
        return next_id

    def get_state(self, time):
        last_state = self.snapshots[0]
        for i in xrange(1, len(self.snapshots)):
            next_state = self.snapshots[i]
            if next_state.time > time:
                break
            else:
                last_state = next_state
        for update in self.updates:
            if update.time > time:
                break
            if update.time > last_state.time:
                last_state.apply(update)
        return last_state

    def get_update(self, start, end):
        result = Update(start)
        for update in self.updates:
            if update.time < start:
                pass
            elif update.time < end:
                result.merge(update)
            else:
                break

    def add_update(self, update):
        self.updates.append(update)
        self.current_state.apply(update)
        for listener in self.listeners_update:
            listener(update)

    def finish(self):
        print "finished loading"
        self.complete = True

    def add_event(self, event):
        self.events.append(event)
        for listener in self.listeners_event:
            listener(event)

    def add_update_listener(self, listener):
        self.listeners_update.append(listener)

    def add_event_listener(self, listener):
        self.listeners_event.append(listener)

