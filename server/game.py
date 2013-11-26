import copy
from utils import enum

SNAPSHOT_INTERVAL = 1000


class UpdateIterator:
    def __init__(self, game, time):
        self.game = game
        self.current = Update(time)
        self.next = Update(time)
        self.iterator = game.updates.__iter__()
        while self.next is not None and self.next.time < self.current.time:
            self.advance()

    def advance(self):
        try:
            self.next = self.iterator.next()
        except StopIteration:
            self.next = None


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

    def update_iterator(self, time):
        return UpdateIterator(self, time)

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
    def __init__(self, type, id, attribute = "", value = None):
        self.type = type
        self.id = id # object id
        self.attribute = attribute  # (object,attribute)
        self.value = value  # None new value

    def get_data(self):
        data = dict()
        data["Type"] = self.type
        data["ID"] = self.id
        if self.type is ChangeType.CREATE:
            data["Attribute"] = self.attribute
        elif self.type is ChangeType.SET:
            data["Attribute"] = self.attribute
            data["Value"] = self.value
        return data


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
            print "ERROR: Applied past update {},{}".format(update.time, self.time)
        self.time = update.time
        for change in update.changes:
            if change.type is ChangeType.CREATE:
                if change.id in self.data:
                    print "Trying to create existing object"
                self.data[change.id] = dict()
                self.data[change.id]["type"] = change.attribute
            elif change.type is ChangeType.SET:
                self.data[change.id][change.attribute] = change.value
            elif change.type is ChangeType.DELETE:
                if change.id not in self.data:
                    print "Trying to delete non-existing object"
                del self.data[change.id]
            else:
                print "Bad change type"

    def get(self, id, attribute):
        if id not in self.data:
            print "Bad Id {}".format(id)
        if attribute not in self.data[id]:
            return None
        return self.data[id][attribute]