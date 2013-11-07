#!/usr/bin/env python
import copy


class Game:
    def __init__(self, id_):
        self.id = id_
        self.snapshots = []
        self.updates = []
        self.messages = []
        self.listener_update = None
        self.listener_event = None
        self.complete = True
        self.latest_update = 0

    def get_state(self, time):
        last_state = self.snapshots[0]
        for i in xrange(1, len(self.snapshots)-1):
            next_state = self.snapshots[i]
            if next_state.time > time:
                break
            else:
                last_state = next_state
        # apply updates
        return last_state

    def get_update(self, start, end):
        result = Update(start,start)
        for update in self.updates:
            if update.time < start:
                pass
            elif update.time < end:
                result.merge(update)
            else:
                break

    def initialise(self, state):
        self.snapshots = []
        self.snapshots.append(state)
        self.complete = False

    def add_update(self, update):
        self.updates.append(update)
        self.listener_update(update)
        if update.time > self.latest_update:
            self.latest_update = update.time
        else:
            print "Error: added past update"

    def finish(self):
        print "finished loading"
        self.complete = True

    def add_event(self, event):
        self.messages.append(event)
        self.listener_event(event)

    def set_update_listener(self, listener):
        self.listener_update = listener

    def set_event_listener(self, listener):
        self.listener_event = listener


class Change:
    def __init__(self, property_, value):
        self.property = property_  # []  list of nested identifiers
        self.value = value  # None new value

    def compare_property(self, change2):
        index = 0
        for identifier in self.property:
            if not index < len(change2.property):
                break
            if identifier is not change2.property[index]:
                break
            else:
                index += 1
        if index == 0:
            pass
        elif index is len(self.property) and index is len(change2.property):
            pass
        elif index is len(self.property) and index < len(change2.property):
            pass
        elif index < len(self.property) and index is len(change2.property):
            pass
        elif index < len(self.property) and index < len(change2.property):
            pass

    def get_data(self):
        data = dict()
        data["Property"] = self.property
        data["Value"] = self.value
        return data


class Update:
    def __init__(self, origin, time, changes=[]):
        self.origin = origin
        self.time = time
        self.changes = copy.deepcopy(changes)

    def merge(self, update2):
        if self.time > update2.time:
            return Update.merge(update2, self)
        if update2.origin < self.time:
            print "Merging Bad Updates"

        for change in update2.changes:
            if False:  # same property changed
                pass  # add changes
        return self

    def add_change(self, change):
        self.changes.append(change)

    def get_data(self):
        data = dict()
        data["Origin"] = self.origin
        data["Time"] = self.time
        data["Changes"] = []
        for change in self.changes:
            data["Changes"].append(change.get_data())
        return data


class State(dict):
    def __init__(self, time):
        self.time = time
        self.state = dict()

    def apply(self, update):
        pass

    def get_data(self):
        return self.state