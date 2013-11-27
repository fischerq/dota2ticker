import simplejson as json
from threading import Thread
import socket
import os


class LoaderServer:
    def __init__(self, game_id, port):
        print "a"
        self.game_id = game_id
        Thread(self.accept_listeners(port)).start()
        self.listeners = []
        print "a"

    def accept_listeners(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", port))
        server.listen(5)
        while True:
            conn, addr = server.accept()
            data = conn.recv(1024)
            msg = data.split(" ")
            if len(msg) is 2 and msg[0] is "LISTEN" and msg[1] is self.game_id:
                conn.sendall("ACCEPT")
                self.listeners.append(conn)
            else:
                conn.sendall("DENIED")
                conn.close()

    def send_event(self, event):
        msg = "EVENT {}".format(json.dumps(event.serialize()))
        for listener in self.listeners:
            listener.sendall(msg)

    def send_update(self, update):
        msg = "UPDATE {}".format(json.dumps(update.serialize()))
        for listener in self.listeners:
            listener.sendall(msg)

    def finish(self):
        msg = "END"
        for listener in self.listeners:
            listener.sendall(msg)