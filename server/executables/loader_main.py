from server.loader.gameloader import ReplayLoader
from server.loader.loaderserver import LoaderServer
from server.connectionserver.registrationproxy import RegistrationProxy
import sys

game_id = int(sys.argv[1])
loader_port = int(sys.argv[2])
registration_port = int(sys.argv[3])

print "Created Loader for game {}, communicating on file {}, registering at {}".format(game_id, loader_port, registration_port)

loader_server = LoaderServer(game_id, loader_port)
loader = ReplayLoader(game_id, loader_server)
registration_proxy = RegistrationProxy(registration_port)
registration_proxy.add_loader(loader_server)
loader.load()