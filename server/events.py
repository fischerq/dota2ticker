from utils import enum

EventTypes = enum("StateChange",
                  "ChatEvent")

class Event:
    def __init__(self, time, importance, event_type):
        self.time = time
        self.importance = importance
        self.type = event_type
        self.data = dict()


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