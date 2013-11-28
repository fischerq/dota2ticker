import server.protocols.loader as ServerProtocol
import simplejson as json
from threading import Thread
import socket


class LoaderServer:
    def __init__(self, game_id, port):
        self.game_id = game_id
        self.port = port
        Thread(target=self.accept_listeners).start()
        self.listeners = []

    def accept_listeners(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", self.port))
        server.listen(5)
        while True:
            conn, addr = server.accept()
            data = conn.recv(1024)
            message = ServerProtocol.parse_message(data)
            if ServerProtocol.check(message) \
                and message["Type"] is ServerProtocol.MessageTypes.LISTEN \
                and message["GameID"] == self.game_id:
                print "Accepted listener for loader {}".format(self.game_id)
                conn.sendall(ServerProtocol.AcceptedMessage())
                self.listeners.append(conn)
            else:
                print message
                conn.sendall(ServerProtocol.RejectedMessage())
                conn.close()

    def send_event(self, event):
        serialized = json.dumps(event.serialize())
        msg = "EVENT {} {}".format(len(serialized), serialized)
        for listener in self.listeners:
            listener.sendall(msg)

    def send_update(self, update):
        serialized = json.dumps(update.serialize())
        msg = "UPDATE {} {}".format(len(serialized), serialized)
        for listener in self.listeners:
            listener.sendall(msg)

    def finish(self):
        msg = "END"
        for listener in self.listeners:
            listener.sendall(msg)