from gevent import monkey; monkey.patch_all(os=False)
from threading import Thread
import socket
import simplejson as json
from server.libs.events import DeserializeEvent
from server.libs.game import DeserializeUpdate


class LoaderProxy:
    def __init__(self, game_id, listener, loader_port):
        self.game_id = game_id
        self.listener = listener
        self.port = loader_port

    def start(self):
        Thread(target=self.listen_to_data).start()

    def listen_to_data(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", self.port))
        s.sendall("LISTEN {}".format(self.game_id))
        data = s.recv(1024)
        if data is "ACCEPTED":
            running = True
            while running:
                data = s.recv(1024)
                while data[-1] is not '}':
                    print "received \"{}\", continuing to receive".format(data)
                    next_data = s.recv(1024)
                    data = ''.join([data,next_data])
                msg = data.split(" ",1)
                if len(msg) is 1 and msg[0] is "END":
                    self.listener.finish()
                    running = False
                elif len(msg) is not 2:
                    print "Bad message: {}".format(data)
                    running = False
                elif msg[0] is "EVENT":
                    self.listener.register_event(DeserializeEvent(json.loads(msg[1])))
                elif msg[0] is "UPDATE":
                    self.listener.register_update(DeserializeUpdate(json.loads(msg[1])))
            s.close()
        else:
            print data
            s.close()
            return