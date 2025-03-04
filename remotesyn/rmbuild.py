#!/usr/bin/env python3

import configparser
import sys
import paramiko
import base64
import struct
import os
import json
import signal

def cmd(cmd, channel):
    channel.exec_command(base64.encodebytes(cmd))

def sstr(s):
    return struct.pack('>I', len(s)) + s.encode('utf-8')
    
def rstr(channel):
    l = struct.unpack('>I', channel.recv(4))[0]
    return bytes.decode(channel.recv(l), 'utf-8')

def send_file(channel, file, othername=None):
    print(f"> {file}")
    if not os.path.exists(file):
        print(f"Error: {file} does not exists")
    with open(file, 'rb') as f:
        stat = os.fstat(f.fileno())
        print('  -> fsize', stat.st_size)
        if othername is None:
            othername = file
        fsize = struct.pack('>q', stat.st_size)
        cmd(b'sf'+sstr(othername)+fsize, channel)
        status = channel.recv(3)
        if status!=b'OK\n':
            print('Something went wrong...')
            exit(1)
        i = stat.st_size
        while i>0:
            fdata = f.read(1024)
            i -= 1024
            channel.sendall(fdata)

def recv_file(channel, file):
    print(f"< {file}")
    if os.path.dirname(file) != '':
        os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, 'wb') as f:
        cmd(b'rf'+sstr(file), channel)
        while True:
            status = channel.recv(2)
            if status != b'\x00\x00':
                break
        if status!=b'OK':
            msg = channel.recv(1024)
            if bytes.decode(msg, 'ascii').startswith('File not found'):
                print("Error: File not found...")
                return
            else:
                print("Error:", bytes.decode(msg, 'ascii'))
                exit(1)
        fsize = channel.recv(8)
        fsize = struct.unpack('>q', fsize)[0]
        print('  -> fsize', fsize)
        while fsize>0:
            f.write(channel.recv(1024))
            fsize -= 1024

def recv_dir(channel, dr):
    print("<<<", dr)
    cmd(b'ls'+sstr(dr), channel)
    while True:
        status = channel.recv(1)
        if status != b'\x00':
            break
    status += channel.recv(1)
    if status!=b'OK':
        msg = channel.recv(1024)
        print("Error:", bytes.decode(msg, 'ascii'))
        exit(1)
    ls = rstr(channel)
    for p in ls.split('\n'):
        tp = p[0]
        name = p[1:]
        if tp=='d':
            if name.startswith('.'):
                continue
            recv_dir(channel, f'{dr}/{name}')
        else:
            recv_file(channel, f'{dr}/{name}')

def print_help():
    print("Unified FPGA synthesizer frontend - remote execution\r\n(c) Joppe Blondel - 2022\r\n")
    print(f"Usage: {sys.argv[0]} [ OPTIONS ] target ...")
    print("")
    print("Options:")
    print("  -h                 Show this help message")
    print("  -c <file>          Configuration file, defaults to project.cfg")

def main():
    # Parse arguments
    i = 1
    nextarg = None
    configpath = 'project.cfg'
    targets = []
    while i<len(sys.argv):
        if nextarg is not None:
            if nextarg=='config':
                configpath = sys.argv[i]
                nextarg = None
            else:
                nextarg = None
        elif sys.argv[i]=='-h':
            print_help()
            exit(0)
        elif sys.argv[i]=='-c':
            nextarg = 'config'
        else:
            targets.append(sys.argv[i])
        i += 1
    if nextarg is not None:
        print("ERROR: expected more arguments")
        exit(1)

    config = configparser.ConfigParser()
    config.read(configpath)

    # Get SSH configuration
    privkey = config.get('server', 'privkey', fallback='__privkey__')
    pubkey = config.get('server', 'pubkey', fallback='__pubkey__')
    hostname = config.get('server', 'hostname', fallback='__hostname__')
    port = config.get('server', 'port', fallback='__port__')
    if privkey=='__privkey__' or pubkey=='__pubkey__' or hostname=='__hostname__' or port=='__port__':
        print("ERROR: Not enough server information in the config file")
        exit(1)

    # Connect to SSH and create channel
    try:
        host_key = paramiko.RSAKey(filename=privkey)
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        trans = paramiko.Transport((hostname, int(port)))
        trans.connect(None, pkey=host_key)
        channel = trans.open_channel('session')
    except paramiko.ssh_exception.SSHException as e:
        print("ERROR: Could not connect to server")
        exit(1)

    subprocesses = []
    stopped = False

    def sighandler(num, frame):
        global stopped
        if num==signal.SIGINT:
            print("\rStopping rbuild")
            stopped = True
            for p in subprocesses:
                p.terminate()
            exit(0)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGALRM, sighandler)

    try:
        for target in targets:
            if stopped:
                break

            # Send project identification
            cmd(b'id' + struct.pack('>q', hash(host_key.get_base64())), channel)
            # Send config
            cmd(b'cf' + sstr(json.dumps({s:dict(config.items(s)) for s in config.sections()})), channel)
            
            print("LOCAL: Target", target)

            toolchain = config.get(f'target.{target}', 'toolchain', fallback='NONE')
            if toolchain=='NONE':
                print("ERROR: No toolchain specified for target")
                exit(1)
            
            try:
                exec(f"from remotesyn.toolchains.{toolchain} import do")
            except ImportError:
                print(f"ERROR: Unknown toolchain '{toolchain}'")
                exit(1)

            # Send all files
            for it in config.items(f"target.{target}"):
                if it[0].startswith('files_'):
                    for f in it[1].split():
                        send_file(channel, f)

            cmd(b'do'+sstr(target), channel)
            while True:
                status = channel.recv(1)
                if status!='b\x00':
                    break
            status += channel.recv(1)
            end = -1
            while end<0:
                data = channel.recv(8)
                end = data.find(b'\x00\xff\x00')
                if end>=0:
                    data = data[0:end]
                print(str(data, 'utf-8'), end='', flush=True)
                sys.stdout.flush()

            ret = int.from_bytes(channel.recv(4), 'big')

            # Receive output dir
            recv_dir(channel, config.get('project', 'out_dir', fallback='out'))

            if ret!=0:
                print("ERROR: toolchain returned with", ret)
                exit(ret)

        cmd(b'ex', channel)

    except paramiko.ssh_exception.SSHException as e:
        print("ERROR: Connection error...", e)
        for p in subprocesses:
            p.kill()
        exit(0)


if __name__=="__main__":
    main()