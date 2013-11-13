#!/usr/bin/env python
import copy

SNAPSHOT_INTERVAL = 1000
class Game:
    def __init__(self,):
        self.listener_update = None
        self.listener_event = None

        self.current_state = State(0)
        self.snapshots = []
        self.snapshots.append(self.current_state)
        self.updates = []
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
        self.listener_update(update)

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


from utils import enum

ChangeType = enum(
    "CREATE",
    "SET",
    "DELETE"
)


class Change:
    def __init__(self, type, id, attribute = "", value = None):
        self.type = type
        self.id = id # object id
        self.attribute = attribute  # (object,attribute)
        self.value = value  # None new value

    def get_data(self):
        data = dict()
        data["Type"] = self.type
        data["ID"] = self.ID
        data["Attribute"] = self.attribute
        data["Value"] = self.value
        return data


class Update:
    def __init__(self, time, changes=[]):
        self.time = time
        self.changes = copy.deepcopy(changes)

    def merge(self, update2):
        if self.time > update2.time:
            return Update.merge(update2, self)

        added_changes = []
        for new_change in update2.changes:
            found = False
            for my_change in self.changes:
                if my_change.type is ChangeType.SET and new_change.type is ChangeType.SET and \
                    my_change.id is new_change.id and \
                    my_change.attribute is new_change.attribute:  # same property changed
                    my_change.value = new_change.value
                    found = True
                    break
            if not found:
                added_changes.append(new_change)

        self.changes.extend(added_changes)

        return self

    def get_data(self):
        data = dict()
        data["Time"] = self.time
        data["Changes"] = []
        for change in self.changes:
            data["Changes"].append(change.get_data())
        return data


class State(dict):
    def __init__(self, time):
        self.time = time
        self.data = dict()

    def apply(self, update):
        if update.time < self.time:
            print "ERROR: Applied past update"

        self.time = update.time
        for change in update.changes:
            self.data[change.key] = change.value