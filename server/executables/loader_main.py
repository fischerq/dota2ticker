from server.loader.replayloader import ReplayLoader
from server.loader.loaderserver import LoaderServer
from server.connectionserver.registrationproxy import RegistrationProxy
import sys
import subprocess

game_id = int(sys.argv[1])
loader_port = int(sys.argv[2])
registration_port = int(sys.argv[3])

print "Created Loader for game {}, communicating on file {}, registering at {}".format(game_id, loader_port, registration_port)

loader_server = LoaderServer(game_id, loader_port)
loader = ReplayLoader(game_id, loader_server)

subprocess.Popen(["python", "server/executables/dumper_main.py", str(game_id), str(loader_port)])

registration_proxy = RegistrationProxy(registration_port)
registration_proxy.add_loader(loader_server)

loader.load()

print "Closed loader"
connection_server = RegistrationProxy(registration_port)
connection_server.remove_loader(loader_server)