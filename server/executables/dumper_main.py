import sys

from server.dumper.jsondumper import GameDumper
from server.loader.loaderproxy import LoaderProxy

import os
game_id = int(sys.argv[1])
loader_port = int(sys.argv[2])

print "dumper dir: {}".format(os.getcwd())
print "dumper created for game {}".format(game_id)

dumper = GameDumper(game_id)

loader = LoaderProxy(game_id, dumper, loader_port)
loader.start()

loader.thread.join()