from server.protocols import check_field
from server.libs.utils import enum

MessageTypes = enum(
    "CONNECT",  # C: GameID
    "GAME_AVAILABILITY",  # S: Availability
    "CLIENT_INFO"  # S: Host, PortRequest, PortListener, ClientID
)

AvailabilityStates = enum(
    "AVAILABLE",
    "PENDING",
    "UNAVAILABLE"
)


def check(message):
    if message is None:
        return False
    if "Type" not in message:
        print "Bad message: no type"
        return False
    result = True
    if message["Type"] is MessageTypes.CONNECT:
        result = check_field(message, "GameID")
    elif message["Type"] is MessageTypes.CLIENT_INFO:
        result = check_field(message, "Host") and\
            check_field(message, "Port") and \
            check_field(message, "ClientID")
    elif message["Type"] is MessageTypes.GAME_AVAILABILITY:
        result = check_field(message, "Availability")
    return result


def GameAvailabilityMessage(availability):
    message = dict()
    message["Type"] = MessageTypes.GAME_AVAILABILITY
    message["Availability"] = availability
    return message


def ClientInfoMessage(host, port, id, game_id):
    message = dict()
    message["Type"] = MessageTypes.CLIENT_INFO
    message["Host"] = host
    message["Port"] = port
    message["ClientID"] = id
    message["ClientID"] = id
    message["GameID"] = game_id
    return message