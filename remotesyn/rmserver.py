#!/usr/bin/env python3

import configparser
import signal
import sys
import time
import subprocess
from types import NoneType
import paramiko
import base64
import struct
import os
import json
import threading
import socket
import shutil
import fcntl
import traceback

# List of running threads
threads = []
running = False

def sighandler(sig, frame):
    global threads
    global running

    print("\rStopping server")
    running = False
    for t in threads:
        t.stop();

class FileTransferSF(threading.Thread):
    def __init__(self, channel, fname, identifier, fsize):
        threading.Thread.__init__(self)
        self.channel = channel
        self.fname = fname
        self.identifier = identifier
        self.fsize = fsize
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        with open(f"{self.identifier}/{self.fname}", 'wb') as f:
            fsize = self.fsize
            while fsize>0 and self.running:
                fdata = self.channel.recv(1024)
                f.write(fdata)
                fsize -= 1024

class FileTransferRF(threading.Thread):
    def __init__(self, channel, fname, identifier):
        threading.Thread.__init__(self)
        self.channel = channel
        self.fname = fname
        self.identifier = identifier
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        with open(f"{self.identifier}/{self.fname}", 'rb') as f:
            stat = os.fstat(f.fileno())
            print('  -> fsize', stat.st_size)
            fsize = struct.pack('>q', stat.st_size)
            i = stat.st_size
            self.channel.sendall(b'OK'+fsize)
            while i>0 and self.running:
                fdata = f.read(1024)
                self.channel.sendall(fdata)
                i -= 1024

class DoLogger(threading.Thread):
    def __init__(self, channel, p, identifier):
        threading.Thread.__init__(self)
        self.channel = channel
        self.p = p
        self.identifier = identifier
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        while self.p.poll() is None:
            d = os.read(self.p.stdout.fileno(), 1024)
            self.channel.sendall(d)
        res = self.p.wait()
        self.channel.sendall(b'\x00\xff\00')
        self.channel.sendall(struct.pack('>I', res))

class SSHServer(paramiko.ServerInterface):
    def __init__(self, authorized):
        self.event = threading.Event()
        self.authorized = authorized
        self.identifier = ''
        self.subprocesses = []
        self.threads = []

    def stop(self):
        self.event.set()
        for s in self.subprocesses:
            s.kill()
        for t in self.threads:
            if type(t) is not NoneType:
                t.stop()

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
        try:
            command = base64.decodebytes(command)
            cmd = command[:2]
            data = command[2:]

            # Identifier
            if cmd==b'id':
                identifier = struct.unpack('>q', data[:8])[0]
                self.identifier = str(identifier)
                print('>', identifier)
                # Create directory
                if os.path.exists(str(identifier)):
                    shutil.rmtree(str(identifier))
                os.mkdir(str(identifier))
            
            # Exit
            elif cmd==b'ex':
                print('<', self.identifier)
                self.stop()

            # Config
            elif cmd==b'cf':
                cnf, data = self.rstr(data)
                self.config = configparser.ConfigParser()
                self.config.read_dict(json.loads(cnf))

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
                t = FileTransferSF(channel, fname, self.identifier, fsize)
                self.threads.append(t)
                t.start()

            # Receive file
            elif cmd==b'rf':
                fname, data = self.rstr(data)
                print('<<', fname, self.identifier)
                if not os.path.exists(f"{self.identifier}/{fname}"):
                    channel.sendall(b'ERFile not found')
                else:
                    t = FileTransferRF(channel, fname, self.identifier)
                    self.threads.append(t)
                    t.start()

            # Execute rbuild
            elif cmd==b'do':
                args, data = self.rstr(data)
                print('[]', args)
                with open(f"{self.identifier}/project.cfg", "w") as f:
                    self.config.write(f)
                p = subprocess.Popen(f"rbuild -c project.cfg {args}", shell=True, cwd=f'{self.identifier}', stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                self.subprocesses.append(p)

                t = DoLogger(channel, p, self.identifier)
                self.threads.append(t)
                t.start()

                channel.sendall(b'OK')


            return True

        except Exception as e:
            global running
            if running:
                print("ERROR: Unknown error:", e)
                traceback.print_exception(type(e), e, e.__traceback__)
            return False

class Connection(threading.Thread):
    def __init__(self, sock, addr, host_key, authorized):
        threading.Thread.__init__(self)
        self.sock = sock
        self.addr = addr
        self.host_key = host_key
        self.authorized = authorized
        self.running = False
        print("Connection from", addr)

    def stop(self):
        self.server.event.set()
        self.server.stop()

    def clean(self):
        pass

    def run(self):
        transport = paramiko.Transport(self.sock)
        transport.set_gss_host(socket.getfqdn(""))
        transport.load_server_moduli()
        transport.add_server_key(self.host_key)
        server = SSHServer(self.authorized)
        transport.start_server(server=server)
        self.server = server
        while not server.event.is_set():
            if not transport.is_alive():
                print("Connection", self.addr, "is broken from other end")
                server.stop()
                break
            time.sleep(0.2)
        else:
            print("Connection", self.addr, "closed")

        print("Deleting directory")
        shutil.rmtree(server.identifier, True)

        transport.close()

def print_help():
    print("Unified FPGA synthesizer frontend - remote execution server\r\n(c) Joppe Blondel - 2022\r\n")
    print(f"Usage: {sys.argv[0]} [ OPTIONS ] host port privkey pubkey authorized_hosts")
    print("")
    print("Options:")
    print("  -h                 Show this help message")

def main():
    global running

    # Parse arguments
    i = 1
    host = ''
    port = ''
    pubkey = ''
    privkey = ''
    authorized_f = ''
    while i<len(sys.argv):
        if sys.argv[i]=='-h':
            print_help()
            exit(0)
        else:
            if host=='':
                host = sys.argv[i]
            elif port=='':
                port = sys.argv[i]
            elif privkey=='':
                privkey = sys.argv[i]
            elif pubkey=='':
                pubkey = sys.argv[i]
            elif authorized_f=='':
                authorized_f = sys.argv[i]
        i += 1

    signal.signal(signal.SIGINT, sighandler)

    # Load SSH settings
    host_key = paramiko.RSAKey(filename=privkey)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, int(port)))
    sock.settimeout(0.2)
    sock.listen(100)
    # Get authorized hosts
    with open(authorized_f, 'r') as f:
        authorized = f.read().split('\n')

    running = True
    while running:
        try:
            client, addr = sock.accept()
            conn = Connection(client, addr, host_key, authorized)
            conn.start()
            threads.append(conn)
        except TimeoutError as e:
            pass

    for t in threads:
        t.join()
        t.clean()


if __name__=="__main__":
    main()