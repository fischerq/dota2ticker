from server.libs.utils import enum

EventTypes = enum("StateChange",
                  "ChatEvent",
                  "DraftEvent",
                  "TextEvent")


class Event:
    def __init__(self, time, importance, event_type):
        self.time = time
        self.importance = importance
        self.data = dict()
        self.data["Time"] = time
        self.data["Type"] = event_type

    def serialize(self):
        serialized = dict()
        serialized["time"] = self.time
        serialized["importance"] = self.importance
        serialized["data"] = self.data
        return serialized


def DeserializeEvent(serialized):
    event = Event(0,0,None)
    event.time = serialized["time"]
    event.importance = serialized["importance"]
    event.data = serialized["data"]
    return event

def StateChange(time, state):
    event = Event(time, 10, EventTypes.StateChange)
    event.data["State"] = state
    return event


def ChatEvent(time, type, value, player_ids):
    event = Event(time, 10, EventTypes.StateChange)
    event.data["Type"] = type
    event.data["Value"] = value
    event.data["PlayerIDs"] = player_ids
    return event


def TextEvent(time, text):
    event = Event(time, 10, EventTypes.TextEvent)
    event.data["Text"] = text
    return event


def DraftEvent(time, team, action, hero, time_used):
    event = Event(time, 20, EventTypes.DraftEvent)
    event.data["Team"] = team
    event.data["Action"] = action
    event.data["Hero"] = hero
    event.data["TimeUsed"] = time_used
    return event
