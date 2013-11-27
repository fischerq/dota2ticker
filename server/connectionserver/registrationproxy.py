import socket


class RegistrationProxy:
    def __init__(self, port):
        self.port = port

    def add_game_server(self, server):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.port))
        s.send("GAME_SERVER {} {} {}".format(server.host, server.port, server.game_id))
        data = s.recv(1024)
        s.close()
        if data is "ACCEPTED":
            return True
        else:
            print "GS registration failed: {}".format(data)
            return False

    def add_loader(self, loader):
        print "registering loader"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.port))
        print "LOADER {} {}".format(loader.game_id, loader.port)
        s.send("LOADER {} {}".format(loader.game_id, loader.port))
        data = s.recv(1024)
        s.close()
        if data is "ACCEPTED":
            print "loader registration succeeded: {}".format(data)
            return True
        else:
            print "loader registration failed: {}".format(data)
            return False