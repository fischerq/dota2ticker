#!/usr/bin/env python

from utils import enum

#message types
MessageType = enum(
    "CONNECT",  # C: GameID
    "CLIENT_INFO",  # S: Host, PortRequest, PortListener, ClientID
    "REJECT_CONNECTION",  # S:
    "REGISTER",  # C: ClientID, GameID
    "CONFIRM",  # S: Data
    "CONFIGURE",  # C: Setting, Value
    "GETSTATE",  # C: Time
    "SUBSCRIBE",  # C: Time
    "STATE",  # S: State
    "UPDATE",  # S: Update
    "EVENT"  # S: Event
    )

SubscribeMode = enum(
    "IMMEDIATE",
    "COMPRESSED",
    "FIXED"
)

#for k in vars(MessageType).keys():
#    print "{}:{}".format(k,vars(MessageType)[k])


def check_field(message, field):
    if field not in message:
        print "{} is missing {}".format(message["Type"], field)
        return False
    else:
        return True


def check(message):
    if message is None:
        return False
    if "Type" not in message:
        print "Bad message: no type"
        return False
    result = True
    if message["Type"] is MessageType.CONNECT:
        result = check_field(message, "GameID")
    elif message["Type"] is MessageType.CLIENT_INFO:
        result = check_field(message, "Host") and\
            check_field(message, "PortRequest") and \
            check_field(message, "PortListener") and\
            check_field(message, "ClientID")
    elif message["Type"] is MessageType.REJECT_CONNECTION:
        result = True
    elif message["Type"] is MessageType.REGISTER:
        result = check_field(message, "ClientID") and\
            check_field(message, "GameID")
    elif message["Type"] is MessageType.CONFIRM:
        result = check_field(message, "Data")
    elif message["Type"] is MessageType.CONFIGURE:
        result = check_field(message, "Setting") and\
            check_field(message, "Value")
    elif message["Type"] is MessageType.GETSTATE:
        result = check_field(message, "Time")
    elif message["Type"] is MessageType.SUBSCRIBE:
        result = check_field(message, "Time") and\
            check_field(message, "MessageDetail") and\
            check_field(message, "Mode")
        if message["Mode"] is SubscribeMode.FIXED:
            result = result and check_field(message, "Step")
    elif message["Type"] is MessageType.STATE:
        result = check_field(message, "State")
    elif message["Type"] is MessageType.UPDATE:
        result = check_field(message, "Update")
    elif message["Type"] is MessageType.EVENT:
        result = check_field(message, "Event")
    return result

next_id = 0


def generate_id():
    #generate unique ID
    global next_id
    id_ = next_id
    next_id += 1
    return id_
