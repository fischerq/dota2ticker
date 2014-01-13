from server.protocols import check_field
from server.libs.utils import enum

MessageTypes = enum (
    "LISTEN",
    "ACCEPTED",
    "REJECTED",
    "EVENT",
    "UPDATE",
    "END"
)


def check(message):
    if message is None:
        return False
    if "Type" not in message:
        print "Bad message: no type"
        return False
    result = True
    if message["Type"] is MessageTypes.LISTEN:
        result = check_field(message, "GameID")
    elif message["Type"] is MessageTypes.ACCEPTED:
        pass
    elif message["Type"] is MessageTypes.REJECTED:
        pass
    return result


def ListenMessage(game_id):
    return "{} {}".format(MessageTypes.LISTEN, game_id)


def AcceptedMessage():
    return "{} ".format(MessageTypes.ACCEPTED)


def RejectedMessage():
    return "{} ".format(MessageTypes.REJECTED)


def parse_message(data):
    args = data.split(" ")
    message = dict()
    if args[0] == MessageTypes.LISTEN:
        message["Type"] = MessageTypes.LISTEN
        if len(args) >= 2:
            message["GameID"] = int(args[1])
    elif args[0] == MessageTypes.ACCEPTED:
        message["Type"] = MessageTypes.ACCEPTED
    elif args[0] == MessageTypes.REJECTED:
        message["Type"] = MessageTypes.REJECTED
    return message