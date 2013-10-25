#!/usr/bin/env python

from utils import enum

#message types
MessageType = enum(
    "CONNECT", #GameID
    "CLIENT_INFO", #Host, PortRequest, PortListener, ClientID
    "REJECT_CONNECTION", #
    "REGISTER", #ClientID, GameID
    "CONFIGURE", #Setting, Value
    "GETSTATE", #Time
    "SUBSCRIBE", #Time, MessageDetail, Mode, [Interval]
    "STATE", #State
    "UPDATE", #Update
    "EVENT" #Event
    )

SubscribeMode = enum(
    "IMMEDIATE",
    "COMPRESSED",
    "FIXED"
)

#for k in vars(MessageType).keys():
#    print "{}:{}".format(k,vars(MessageType)[k])

def checkField(message, field):
    if field not in message:
        print "{} is missing {}".format(message["Type"], field)
        return False
    else:
        return True
def check(message):
    if "Type" not in message:
        print "Bad message: no type"
        return False
    result = True
    if message["Type"] is MessageType.CONNECT:
        result = checkField(message, "GameID")
    elif message["Type"] is MessageType.CLIENT_INFO:
        result = checkField(message, "Host") and\
                 checkField(message, "PortRequest") and \
                 checkField(message, "PortListener") and\
                 checkField(message, "ClientID")
    elif message["Type"] is MessageType.REJECT_CONNECTION:
        result = True
    elif message["Type"] is MessageType.REGISTER:
        result = checkField(message, "ClientID") and\
                 checkField(message, "GameID")
    elif message["Type"] is MessageType.CONFIGURE:
        result = checkField(message, "Setting") and\
                 checkField(message, "Value")
    elif message["Type"] is MessageType.GETSTATE:
        result = checkField(message, "Time")
    elif message["Type"] is MessageType.SUBSCRIBE:
        result = checkField(message, "Time") and\
                 checkField(message, "MessageDetail") and\
                 checkField(message, "Mode")
        if(message["Mode"] is SubscribeMode.FIXED):
            result = result and checkField(message, "Step")
    elif message["Type"] is MessageType.STATE:
        result = checkField(message, "State")
    elif message["Type"] is MessageType.UPDATE:
        result = checkField(message, "Update")
    elif message["Type"] is MessageType.EVENT:
        result = checkField(message, "Event")
    return result

next_id = 0

def generateID():
    #generate unique ID
    global next_id
    id_ = next_id
    next_id += 1
    return id_
