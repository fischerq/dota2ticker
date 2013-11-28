from server.protocols import check_field
from server.libs.utils import enum

MessageTypes = enum(
    "REGISTER",  # C: ClientID, GameID
    "CONFIRM",  # S: Data
    "CONFIGURE",  # C: Setting, Value
    "GETSTATE",  # C: Time
    "SUBSCRIBE",  # C: Time
    "STATE",  # S: State
    "UPDATE",  # S: Update
    "EVENT",  # S: Event
    "ERROR", # S: Msg
    )


SubscribeModes = enum(
    "CURRENT",
    "PAST"
)


def check(message):
    if message is None:
        return False
    if "Type" not in message:
        print "Bad message: no type"
        return False
    result = True
    if message["Type"] is MessageTypes.REGISTER:
        result = check_field(message, "GameID")
    elif message["Type"] is MessageTypes.CONFIRM:
        result = check_field(message, "Data")
    elif message["Type"] is MessageTypes.CONFIGURE:
        result = check_field(message, "Setting") and\
            check_field(message, "Value")
    elif message["Type"] is MessageTypes.GETSTATE:
        result = check_field(message, "Time")
    elif message["Type"] is MessageTypes.SUBSCRIBE:
        result = check_field(message, "Time") and\
            check_field(message, "Mode")
    elif message["Type"] is MessageTypes.STATE:
        result = check_field(message, "State")
    elif message["Type"] is MessageTypes.UPDATE:
        result = check_field(message, "Update")
    elif message["Type"] is MessageTypes.EVENT:
        result = check_field(message, "Event")
    return result




def ConfirmMessage():
    message = dict()
    message["Type"] = MessageTypes.CONFIRM
    return message


def ErrorMessage(message):
    message = dict()
    message["Type"] = MessageTypes.ERROR
    message["Message"] = message
    return message


def StateMessage(state):
    message = dict()
    message["Type"] = MessageTypes.STATE
    message["Time"] = state.time
    message["State"] = state.data
    return message


def UpdateMessage(update):
    message = dict()
    message["Type"] = MessageTypes.UPDATE
    message["Time"] = update.time
    message["Update"] = update.serialize()
    return message


def EventMessage(event):
    message = dict()
    message["Type"] = MessageTypes.EVENT
    message["Time"] = event.time
    message["Event"] = event.data
    return message