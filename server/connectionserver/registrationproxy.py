import socket


class RegistrationProxy:
    def __init__(self, port):
        self.port = port

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("localhost", self.port))
            return s
        except socket.error as e:
            print "Connecting to connServ failed: {}".format(e)
            return None


    def add_game_server(self, server):
        s = self.connect()
        try:
            s.send("GAME_SERVER {} {} {}".format(server.public_address, server.port, server.game_id))
            data = s.recv(1024)
            s.close()
            if data == "ACCEPTED":
                return True
            else:
                print "GS registration failed: {}".format(data)
                return False
        except socket.error:
            return False

    def remove_game_server(self, server):
        s = self.connect()
        try:
            s.send("REMOVE_GAME_SERVER {}".format(server.game_id))
            data = s.recv(1024)
            s.close()
            if data == "ACCEPTED":
                return True
            else:
                print "GS registration failed: {}".format(data)
                return False
        except socket.error:
            return False

    def add_loader(self, loader):
        print "registering loader"
        s = self.connect()
        try:
            print "LOADER {} {}".format(loader.game_id, loader.port)
            s.send("LOADER {} {}".format(loader.game_id, loader.port))
            data = s.recv(1024)
            s.close()
            if data == "ACCEPTED":
                print "loader registration succeeded: {}".format(data)
                return True
            else:
                print "loader registration failed: {}".format(data)
                return False
        except socket.error:
            return False

    def remove_loader(self, loader):
        print "removing server"
        s = self.connect()
        try:
            print "REMOVE_LOADER {}".format(loader.game_id)
            s.send("REMOVE_LOADER {}".format(loader.game_id))
            data = s.recv(1024)
            s.close()
            if data == "ACCEPTED":
                print "loader registration succeeded: {}".format(data)
                return True
            else:
                print "loader registration failed: {}".format(data)
                return False
        except socket.error:
            return False