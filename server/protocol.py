#!/usr/bin/env python

from utils import enum

#message types
MessageType = enum(
    "CONNECT", #GameID
    "CLIENT_INFO", #Host, PortRequest, PortListener, ClientID
    "REJECT_CONNECTION", #
    "REGISTER", #ClientID, GameID
    "GETSTATE", #Time
    "STATE" #State
    )



def check(message):
    if "Type" not in message:
        print "Bad message: no type"
        return False
    return True

next_id = 0

def generateID():
    #generate unique ID
    id_ = next_id
    next_id += 1
    return id_
