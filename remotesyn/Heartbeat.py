import threading
import time
import base64

class Heartbeat(threading.Thread):
    def __init__(self, channel):
        threading.Thread.__init__(self)
        self.channel = channel
        self.running = True
        self.printing = False
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if self.printing:
                print('.', end='', flush=True)
            self.channel.exec_command(base64.encodebytes(b'hb'))
            time.sleep(2)

class HeartbeatChecker(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.running = True
        self.hb = True
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if not self.hb:
                self.server.active = False
                self.server.event.set()
            self.hb = False
            time.sleep(5)