import copy
from server.libs.utils import enum
from server.libs.events import Event
SNAPSHOT_INTERVAL = 1000


class PastState:
    def __init__(self, game, time):
        self.game = game
        self.time = time
        self.next_update = Update(0)
        self.update_iterator = game.updates.__iter__()
        self.next_event = Event(0, 0, None)
        self.event_iterator = game.events.__iter__()
        while self.next_update is not None and self.next_update.time < self.time:
            print "scrolling upd iterator {}, {}".format(self.next_update.time, self.time)
            self.next_update = PastState.advance_iterator(self.update_iterator)
        while self.next_event is not None and self.next_event.time < self.time:
            self.next_event = PastState.advance_iterator(self.event_iterator)

    @staticmethod
    def advance_iterator(iterator):
        result = None
        try:
            result = iterator.next()
        except StopIteration:
            result = None
        return result

    def pass_time(self, time_change):
        self.time += time_change
        updates = []
        events = []
        while self.next_update is not None and self.next_update.time <= self.time:
            print "updating upd iterator {}, {}".format(self.next_update.time, self.time)
            updates.append(self.next_update)
            self.next_update = PastState.advance_iterator(self.update_iterator)
        while self.next_event is not None and self.next_event.time <= self.time:
            print "updating evt iterator {}, {}".format(self.next_event.time, self.time)
            events.append(self.next_event)
            self.next_event = PastState.advance_iterator(self.event_iterator)
        return updates, events

    def finished(self):
        print "finished {}, {}".format(self.next_update is None, self.next_event is None)
        return self.next_update is None and self.next_event is None


class Game:
    def __init__(self):
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

    def past_state(self, time):
        return PastState(self, time)

    def add_update(self, update):
        if len(self.updates) > 0 and self.updates[-1].time == update.time:
            self.updates[-1].extend(update.changes)
        elif len(self.updates) == 0 or self.updates[-1].time < update.time:
            if self.current_state.time - self.snapshots[-1].time > SNAPSHOT_INTERVAL:
                self.snapshots.append(copy.deepcopy(self.current_state))
            self.updates.append(update)
        else:
            print "adding past change"
        self.current_state.apply(update)

    def finish(self):
        print "finished loading"
        self.complete = True

    def add_event(self, event):
        self.events.append(event)


ChangeType = enum(
    "CREATE",
    "SET",
    "DELETE"
)


class Change:
    def __init__(self, type, id, attribute="", value=None):
        self.type = type
        self.id = id  # object id
        self.attribute = attribute  # (object,attribute)
        self.value = value  # None new value

    def serialize(self):
        data = dict()
        data["Type"] = self.type
        data["ID"] = self.id
        if self.type == ChangeType.CREATE:
            data["Attribute"] = self.attribute
        elif self.type == ChangeType.SET:
            data["Attribute"] = self.attribute
            data["Value"] = self.value
        return data


def DeserializeChange(change):
    if change["Type"] == ChangeType.CREATE:
        return Change(change["Type"], change["ID"], change["Attribute"])
    elif change["Type"] == ChangeType.SET:
        produced = Change(change["Type"], change["ID"], change["Attribute"], change["Value"])
        return produced
    else:
        return Change(change["Type"], change["ID"])


class Update:
    def __init__(self, time, changes=[]):
        self.time = time
        self.changes = copy.copy(changes)

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
        self.time = update2.time
        return self

    def append(self, change):
        self.changes.append(change)

    def extend(self, changes):
        self.changes.extend(changes)

    def serialize(self):
        data = dict()
        data["Time"] = self.time
        data["Changes"] = []
        for change in self.changes:
            data["Changes"].append(change.serialize())
        return data

def DeserializeUpdate(serialized):
    update = Update(serialized["Time"])
    update.changes = []
    for change in serialized["Changes"]:
        update.changes.append(DeserializeChange(change))
    return update


class State(dict):
    def __init__(self, time):
        self.time = time
        self.data = dict()

    def apply(self, update):
        if update.time < self.time:
            print "ERROR: Applied past update {},{}".format(update.time, self.time)
        self.time = update.time
        for change in update.changes:
            if change.type == ChangeType.CREATE:
                if change.id in self.data:
                    print "Trying to create existing object"
                self.data[change.id] = dict()
                self.data[change.id]["type"] = change.attribute
            elif change.type == ChangeType.SET:
                self.data[change.id][change.attribute] = change.value
            elif change.type == ChangeType.DELETE:
                if change.id not in self.data:
                    print "Trying to delete non-existing object"
                del self.data[change.id]
            else:
                print "Bad change type"
                print update.serialize()

    def get(self, id, attribute):
        if id not in self.data:
            print "Bad Id {}".format(id)
        if attribute not in self.data[id]:
            return None
        return self.data[id][attribute]