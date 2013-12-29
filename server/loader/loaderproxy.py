from gevent import monkey; monkey.patch_all()
from threading import Thread
import socket
import simplejson as json
from server.libs.events import DeserializeEvent
from server.libs.game import DeserializeUpdate
import server.protocols.loader as LoaderProtocol

RECEIVE_SIZE = 2048


class LoaderProxy:
    def __init__(self, game_id, listener, loader_port):
        self.game_id = game_id
        self.listener = listener
        self.port = loader_port
        self.thread = Thread(target=self.listen_to_data)

    def start(self):
        self.thread.start()

    @staticmethod
    def read_until(s, delimiter):
        data = ""
        next_byte = s.recv(1)
        while next_byte != delimiter:
            data += next_byte
            next_byte = s.recv(1)
        return data

    def listen_to_data(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.port))
        try:
            s.sendall("LISTEN {}".format(self.game_id))
            data = s.recv(1024)
        except socket.error as e:
            print "Error when opening loader proxy: {}".format(e)
            s.close()
            return
        message = LoaderProtocol.parse_message(data)
        if LoaderProtocol.check(message) and message["Type"] is LoaderProtocol.MessageTypes.ACCEPTED:
            running = True
            while running:
                data = ""
                try:
                    message_type = LoaderProxy.read_until(s, " ")
                    if message_type == LoaderProtocol.MessageTypes.EVENT or\
                       message_type == LoaderProtocol.MessageTypes.UPDATE:
                        length = int(LoaderProxy.read_until(s, " "))
                        while length > 0:
                            if length > RECEIVE_SIZE:
                                received = s.recv(RECEIVE_SIZE)
                            else:
                                received = s.recv(int(length))
                            data += received
                            length -= len(received)
                except socket.error as e:
                    print "Error receiving as loader proxy: {}".format(e)
                    break
                if message_type == LoaderProtocol.MessageTypes.END:
                    self.listener.finish()
                    running = False
                elif message_type == LoaderProtocol.MessageTypes.EVENT:
                    self.listener.register_event(DeserializeEvent(json.loads(data)))
                elif message_type == LoaderProtocol.MessageTypes.UPDATE:
                    self.listener.register_update(DeserializeUpdate(json.loads(data)))
                else:
                    print "Bad message: {} {}".format(message_type, data)
                    running = False
            s.close()
        else:
            print "Loader proxy registration failed: {}".format(data)
            s.close()
            return