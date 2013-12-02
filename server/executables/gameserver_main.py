import sys

from server.connectionserver.registrationproxy import RegistrationProxy
from server.gameserver.gameserver import GameServer
from server.loader.loaderproxy import LoaderProxy

game_id = int(sys.argv[1])
port = int(sys.argv[2])
registration_port = int(sys.argv[3])
loader_port = int(sys.argv[4])

print "Started gameserver for game {} at {}, registering at {}, loading from {}".format(port, game_id, registration_port, loader_port)
server = GameServer("0.0.0.0", port, game_id)

loader = LoaderProxy(game_id, server, loader_port)
loader.start()

connection_server = RegistrationProxy(registration_port)
connection_server.add_game_server(server)