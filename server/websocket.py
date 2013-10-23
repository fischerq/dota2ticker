#!/usr/bin/env python

import socket
from base64 import b64encode
from hashlib import sha1

from threading import Lock
from threading import Thread

class WebsocketServer:
    def __init__(self, port, accept_handler):
        self.port = port
        self.accept_handler = accept_handler
        self.clients = []
        self.clients_lock = Lock()
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.run = False
        self.run_lock = Lock()
        
    def start(self):
        with self.run_lock:
            if not self.run:
                self.run = True
                Thread(target = self.acceptClients).start()
            else:
                print "WebsocketServer on port {} already running".format(self.port)
        
    def acceptClients(self):
        self.socket.listen(5)
        while 1:
            with self.run_lock:
                if not self.run:
                    break
            socket, address = self.socket.accept()
            print "Connection from: {}".format(address)
            new_connection = WebsocketConnection(socket, address)
            new_connection.handshake()
            Thread(target = self.accept_handler, args = (new_connection,)).start()

    def stop(self):
        with self.run_lock:
            self.run = False
        
OP_CONTINUATION = 0
OP_TEXT = 1
OP_BINARY = 2
OP_CLOSE = 8
OP_PING = 9
OP_PONG = 10

class WebsocketFrameHeader:
    def __init__(self):
        self.fin = 0
        self.rsv = 0
        self.opcode = 0
        self.mask = 0
        self.payload_length = 0
        self.masks = 0
    def encode(self, data):
        frame = ""
        #encode header
        first_byte = (self.fin << 7) | (self.rsv << 4) | self.opcode
        frame += chr(first_byte)
        if self.mask:
            print "masking not implemented, will be ignored"
            self.mask = 0
        second_byte = (self.mask << 7)
        if self.payload_length <= 125:
            second_byte = second_byte | self.payload_length
            frame += chr(second_byte)
        elif self.payload_length >= 126 and self.payload_length <= 65535:
            second_byte = second_byte | 126
            frame += chr(second_byte)
            frame += chr(( self.payload_length >> 8 ) & 255)
            frame += chr(( self.payload_length      ) & 255)
        else:
            second_byte = second_byte | 127
            frame += chr(second_byte)
            for i in range(7, 0, -1):
                frame += chr(( self.payload_length >> (8*i) ) & 255 )
        #encode 
        #masking not implemented
        frame += data
        return frame
    def decode(self, payload):
        decoded_payload = ""
        byte_array = [ord(character) for character in payload]
        i = 0
        while i < len(byte_array):
            if self.mask:
                decoded_payload += ( chr(byte_array[i] ^ self.masks[i % 4]) )
            else:
                decoded_payload += chr(byte_array[i])
            i += 1
        return decoded_payload

    @staticmethod
    def decodeMinimalHeader(header_data):
        header = WebsocketFrameHeader()
        byte_array = [ord(character) for character in header_data]
        header.fin = (byte_array[0] & 128) >> 7
        header.rsv = (byte_array[0] & 114) >> 4
        header.opcode = byte_array[0] & 15
        header.mask = (byte_array[1] & 128) >> 7 
        header.payload_length = byte_array[1] & 127
        return header
    @staticmethod
    def decodeFullHeader(header_data):
        header = WebsocketFrameHeader()
        byte_array = [ord(character) for character in header_data]
        header.fin = (byte_array[0] & 128) >> 7
        header.rsv = (byte_array[0] & 114) >> 4
        header.opcode = byte_array[0] & 15
        header.mask = (byte_array[1] & 128) >> 7 
        header.payload_length = byte_array[1] & 127
        index_first_mask = 2 
        if header.payload_length == 126:
            index_first_mask = 4
            header.payload_length = byte_array[2]<<8 | byte_array[3]
        elif header.payload_length == 127:
            index_first_mask = 10
            header.payload_length = 0
            for i in range(0, 7):
                header.payload_length = frame.payload_length | (byte_array[2+i] << (8*(7-i)) )
        index_first_data_byte = index_first_mask
        if header.mask:
            header.masks = [m for m in byte_array[index_first_mask : index_first_mask+4]]
        return header
    @staticmethod
    def createTextHeader(size):
        header = WebsocketFrameHeader()
        header.fin = 1
        header.rsv = 0
        header.opcode = OP_TEXT
        header.mask = 0 
        header.payload_length = size
        header.masks = None
        return header
    @staticmethod
    def createCloseHeader():
        header = WebsocketFrameHeader()
        header.fin = 1
        header.rsv = 0
        header.opcode = OP_CLOSE
        header.mask = 0 
        header.payload_length = 0
        header.masks = None
        return header

PAYLOAD_LENGTH_2_BYTE = 126
PAYLOAD_LENGTH_8_BYTE = 127

class WebsocketConnection:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address

    @staticmethod
    def parse_headers (data):
        headers = {}
        lines = data.splitlines()
        for l in lines:
            parts = l.split(": ", 1)
            if len(parts) == 2:
                headers[parts[0]] = parts[1]
        return headers

    #handshaking inspired by http://stackoverflow.com/questions/10152290/python-websocket-handshake-rfc-6455
    @staticmethod
    def create_response (key):
        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        response_key = b64encode(sha1(key + GUID).digest())
        return response_key
    
    def handshake(self):
        print "Handshaking..."
        data = self.socket.recv(1024)
        headers = WebsocketConnection.parse_headers(data)
        #print "Got headers:"
        #for k, v in headers.iteritems():
        #    print "{}:{}".format(k,v)
        if "Sec-WebSocket-Protocol" not in headers or headers["Sec-WebSocket-Protocol"] != "dota2ticker":
            print "bad protocol"
        response_key = WebsocketConnection.create_response(headers["Sec-WebSocket-Key"])
        shake = "HTTP/1.1 101 Switching Protocols\r\n"
        shake += "Upgrade: websocket\r\n" 
        shake += "Connection: Upgrade\r\n"
        shake += "Sec-WebSocket-Accept: {}\r\n".format(response_key)
        shake += "Sec-WebSocket-Protocol: dota2ticker\r\n\r\n"
        return self.socket.send(shake)

    def recieve(self):
        header_data = self.socket.recv(2)
        header = WebsocketFrameHeader.decodeMinimalHeader(header_data)
        if header.payload_length == PAYLOAD_LENGTH_2_BYTE:
            header_data += self.socket.recv(2)
        elif header.payload_length == PAYLOAD_LENGTH_8_BYTE:
            header_data += self.socket.recv(8)
        if header.mask:
            header_data += self.socket.recv(4)
        header = WebsocketFrameHeader.decodeFullHeader(header_data)
        payload = self.socket.recv(header.payload_length)
        data = header.decode(payload)
        #continue recieving if message is fragmented
        message_finished = header.fin
        while not header.fin :
            (opcode, data_continued) = self.recieve()
            if(opcode != OP_CONTINUATION):
                print "fragmented message with multiple opcodes"
            data += data_continued
        return (header.opcode, data)
    def send(self, string, operation = OP_TEXT):
        #print "sending {}".format(data)
        if operation == OP_TEXT:
            header = WebsocketFrameHeader.createTextHeader(len(string))
        elif operation == OP_CONTINUATION or operation == OP_CLOSE:
            print "trying to send bad message (opcode {})".format(operation)
        else:
            header = WebsocketFrameHeader()
            header.opcode = operation
            header.payload_length =  len(string)
        message = header.encode(string)
        return self.socket.send(message)
    def close(self):
        message = WebsocketFrameHeader.createCloseHeader().encode()
        self.socket.send(message)
        self.socket.close()
