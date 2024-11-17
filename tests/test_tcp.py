# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys

import socketserver

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"Received from {self.client_address[0]}: {self.data.decode('utf-8')}")
        self.request.sendall(self.data.upper())


# abnormal
def signal_handler(sig, frame):
    print("\nSignal handler called with signal", sig)
    print("Program will exit now.")
    sys.exit(0)


# register
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    with ThreadedTCPServer(("localhost", 9999), MyTCPHandler) as server:
        print("Threaded server is running on localhost:9999")
        server.serve_forever()

