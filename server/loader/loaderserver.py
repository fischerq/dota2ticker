import server.protocols.loader as ServerProtocol
import simplejson as json
from threading import Thread
import socket
import server.config as config


class LoaderServer:
    def __init__(self, game_id, port):
        self.game_id = game_id
        self.port = port
        self.listeners = []
        self.running = True
        Thread(target=self.accept_listeners).start()

    def accept_listeners(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((config.host, self.port))
        server.listen(5)
        while self.running:
            conn, addr = server.accept()
            try:
                data = conn.recv(1024)
                message = ServerProtocol.parse_message(data)
                if ServerProtocol.check(message) \
                    and message["Type"] is ServerProtocol.MessageTypes.LISTEN \
                    and message["GameID"] == self.game_id:
                    print "Accepted listener for loader {}".format(self.game_id)
                    conn.sendall(ServerProtocol.AcceptedMessage())
                    self.listeners.append(conn)
                else:
                    print "rejecting message {}".format(message)
                    conn.sendall(ServerProtocol.RejectedMessage())
                    conn.close()
            except socket.error:
                pass
        for listener in self.listeners:
            listener.close()

    def send(self, listener, msg):
        try:
            listener.sendall(msg)
        except socket.error:
            self.listeners[:] = [l for l in self.listeners if l is not listener]

    def send_event(self, event):
        serialized = json.dumps(event.serialize())
        msg = "EVENT {} {}".format(len(serialized), serialized)
        for listener in self.listeners:
            self.send(listener, msg)

    def send_update(self, update):
        serialized = json.dumps(update.serialize())
        msg = "UPDATE {} {}".format(len(serialized), serialized)
        for listener in self.listeners:
            self.send(listener, msg)

    def finish(self):
        msg = "END"
        for listener in self.listeners:
            self.send(listener, msg)
        self.running = False