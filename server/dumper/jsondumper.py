from server.protocols import game as GameProtocol
import simplejson as json


class GameDumper:
    def __init__(self, id):
        self.file = open("server/data/dumps/{}.json".format(id), "w+")

    def register_event(self, event):
        message = GameProtocol.EventMessage(event)
        self.dump_message(message)

    def register_update(self, update):
        message = GameProtocol.UpdateMessage(update)
        self.dump_message(message)

    def dump_message(self, message):
        self.file.write("{}\n".format(json.dumps(message, separators=(',', ': '), indent=4)))

    def close(self):
        self.file.close()
