import copy
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
        data["ID"] = self.id
        if self.type is ChangeType.SET:
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
            if change.type is ChangeType.CREATE:
                if change.id in self.data:
                    print "Trying to create existing object"
                self.data[change.id] = dict()
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