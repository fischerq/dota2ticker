import sys

from server.dumper.jsondumper import GameDumper
from server.loader.loaderproxy import LoaderProxy


game_id = int(sys.argv[1])
loader_port = int(sys.argv[2])

dump_file = "dumps/{}.json".fromat(game_id)
dumper = GameDumper(dump_file)

loader = LoaderProxy(game_id, dumper, loader_port)
loader.start()