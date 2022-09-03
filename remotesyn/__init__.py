from .exec_ISE import exec_ISE
from .exec_VIVADO import exec_VIVADO
from .exec_REMOTE import exec_REMOTE

from .Heartbeat import Heartbeat, HeartbeatChecker

import sys
import os
import shutil
import subprocess
import paramiko
import socket
import threading
import struct
import base64

class Executer(threading.Thread):
    def __init__(self, args, channel, identifier):
        threading.Thread.__init__(self)
        self.args = args
        self.channel = channel
        self.identifier = identifier
        self.pid = None
    def run(self):
        self.pid = subprocess.Popen(f"../{sys.argv[0]} -l -c project.cfg {self.args}", shell=True, cwd=f'{self.identifier}', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = self.pid.wait()
        self.pid = None
        self.channel.sendall(struct.pack('>I', res))

class FileTransferSF(threading.Thread):
    def __init__(self, channel, fname, identifier, fsize):
        threading.Thread.__init__(self)
        self.channel = channel
        self.fname = fname
        self.identifier = identifier
        self.fsize = fsize
    def run(self):
        with open(f"{self.identifier}/{self.fname}", 'wb') as f:
            fsize = self.fsize
            while fsize>0:
                fdata = self.channel.recv(1024)
                f.write(fdata)
                fsize -= 1024

class FileTransferRF(threading.Thread):
    def __init__(self, channel, fname, identifier):
        threading.Thread.__init__(self)
        self.channel = channel
        self.fname = fname
        self.identifier = identifier
    def run(self):
        with open(f"{self.identifier}/{self.fname}", 'rb') as f:
            stat = os.fstat(f.fileno())
            print('  -> fsize', stat.st_size)
            fsize = struct.pack('>q', stat.st_size)
            i = stat.st_size
            self.channel.sendall(b'OK'+fsize)
            while i>0:
                fdata = f.read(1024)
                self.channel.sendall(fdata)
                i -= 1024

class Server(paramiko.ServerInterface):
    def __init__(self, authorized):
        self.event = threading.Event()
        self.authorized = authorized
        self.active = True
        self.hbchecker = HeartbeatChecker(self)
        self.hbchecker.start()
        self.processes = []

    def stopall(self):
        print("Stop all running processes")
        for p in self.processes:
            if p.pid is not None:
                p.pid.terminate()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED

    def check_auth_publickey(self, username, key):
        keyascii = key.get_base64()
        for auth in self.authorized:
            authascii = auth.split(' ')[1]
            if authascii==keyascii:
                return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

    def rstr(self, b):
        l = struct.unpack('>I', b[:4])[0]
        return (bytes.decode(b[4:4+l], 'utf-8'), b[4+l:])

    def sstr(self, s):
        return struct.pack('>I', len(s)) + s.encode('utf-8')

    def check_channel_exec_request(self, channel, command):
        # self.event.set()
        command = base64.decodebytes(command)
        cmd = command[:2]
        data = command[2:]

        if cmd==b'id':
            identifier = struct.unpack('>q', data[:8])[0]
            self.identifier = str(identifier)
            print('>', identifier)
            # Create directory
            if os.path.exists(str(identifier)):
                shutil.rmtree(str(identifier))
            os.mkdir(str(identifier))

        elif cmd==b'ex':
            print('<', self.identifier)
            #shutil.rmtree(str(self.identifier))
            self.active = False
            self.hbchecker.stop()
            self.event.set()

        elif cmd==b'hb':
            self.hbchecker.hb = True

        # List files
        elif cmd==b'ls':
            dr, data = self.rstr(data)
            print('ls', dr)
            if not os.path.exists(f"{self.identifier}/{dr}"):
                channel.sendall(b'ERFile not found')
            es = []
            for f in os.listdir(f'{self.identifier}/{dr}'):
                if os.path.isfile(f'{self.identifier}/{dr}/{f}'):
                    df = 'f'
                else:
                    df = 'd'
                es.append(f'{df}{f}')
            channel.sendall(b'OK' + self.sstr('\n'.join(es)))

        # Send file
        elif cmd==b'sf':
            fname, data = self.rstr(data)
            fsize = struct.unpack('>q', data)[0]
            print('>>', fname, fsize)
            os.makedirs(os.path.dirname(f"{self.identifier}/{fname}"), exist_ok=True)
            channel.sendall(b'OK\n')
            FileTransferSF(channel, fname, self.identifier, fsize).start()

        # Receive file
        elif cmd==b'rf':
            fname, data = self.rstr(data)
            print('<<', fname)
            if not os.path.exists(f"{self.identifier}/{fname}"):
                channel.sendall(b'ERFile not found')
            else:
                FileTransferRF(channel, fname, self.identifier).start()

        # Execute synth
        elif cmd==b'do':
            args, data = self.rstr(data)
            print('[]', args)
            executer = Executer(args, channel, self.identifier)
            executer.start()
            self.processes.append(executer)

        return True

class Connection(threading.Thread):
    def __init__(self, client, addr, host_key, authorized):
        threading.Thread.__init__(self)
        self.client = client
        self.addr = addr
        self.host_key = host_key
        self.running = True
        self.authorized = authorized
        print(f"Connection from {addr}")

    def stop(self):
        self.running = False
        self.server.event.set()

    def run(self):
        self.running = True
        t = paramiko.Transport(self.client)
        t.set_gss_host(socket.getfqdn(""))
        t.load_server_moduli()
        t.add_server_key(self.host_key)
        server = Server(self.authorized)
        t.start_server(server=server)
        self.server = server

        # Wait for the event
        while server.active:
            server.event.wait(10)

        server.stopall()
        shutil.rmtree(server.identifier)

        t.close()
        print('connection closed')