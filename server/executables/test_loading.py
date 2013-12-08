from server.loader.gameloader import ReplayLoader
import simplejson as json

game_id = 303487989
loader_port = 30010

print "Created Loader for game {}, communicating on file {}".format(game_id, loader_port)


class LoadPrinter:
    def __init__(self):
        pass

    def send_event(self, event):
        serialized = json.dumps(event.serialize())
        print "EVENT {} {}".format(len(serialized), serialized)

    def send_update(self, update):
        serialized = json.dumps(update.serialize())
        print "UPDATE {} {}".format(len(serialized), serialized)

    def finish(self):
        print "END"


loader_server = LoadPrinter()
loader = ReplayLoader(game_id, loader_server)
loader.load()