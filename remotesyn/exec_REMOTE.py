import os
import paramiko
import struct
import base64

from .Heartbeat import Heartbeat

class exec_REMOTE:
    def __init__(self, config, configfile):
        self.config = config
        self.configfile = configfile

        self.privkey = self.config.get('server', 'privkey', fallback='__privkey__')
        self.pubkey = self.config.get('server', 'pubkey', fallback='__pubkey__')
        self.hostname = self.config.get('server', 'hostname', fallback='__hostname__')
        self.port = self.config.get('server', 'port', fallback='__port__')

        self.tc = self.config.get('project', 'toolchain', fallback='ISE')

        if self.privkey=='__privkey__' or self.pubkey=='__pubkey__' or self.hostname=='__hostname__' or self.port=='__port__':
            print("Not enough server information in the config file")
            exit(1)

        self.host_key = paramiko.RSAKey(filename=self.privkey)
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        trans = paramiko.Transport((self.hostname, int(self.port)))
        trans.connect(None, pkey=self.host_key)

        self.channel = trans.open_channel('session')
        self.hbchannel = trans.open_channel('session')

        self.heartbeat = Heartbeat(self.hbchannel)
        self.heartbeat.start()

        # Send project identification
        cmd = b'id' + struct.pack('>q', hash(self.host_key.get_base64()))
        self.channel.exec_command(base64.encodebytes(cmd))

    def __del__(self):
        self.heartbeat.stop()
        self.channel.exec_command(base64.encodebytes(b'ex'))

    def cmd(self, cmd):
        self.channel.exec_command(base64.encodebytes(cmd))

    def sstr(self, s):
        return struct.pack('>I', len(s)) + s.encode('utf-8')

    def rstr(self):
        l = struct.unpack('>I', self.channel.recv(4))[0]
        return bytes.decode(self.channel.recv(l), 'utf-8')

    def recv_dir(self, dr):
        self.cmd(b'ls'+self.sstr(dr))
        status = self.channel.recv(2)
        if status!=b'OK':
            msg = self.channel.recv(1024)
            print("Error:", bytes.decode(msg, 'ascii'))
            exit(1)
        ls = self.rstr()
        for p in ls.split('\n'):
            tp = p[0]
            name = p[1:]
            if tp=='d':
                self.recv_dir(f'{dr}/{name}')
            else:
                self.recv_file(f'{dr}/{name}')

    def send_file(self, file, othername=None):
        print(f"> {file}")
        if not os.path.exists(file):
            print(f"Error: {file} does not exists")
        with open(file, 'rb') as f:
            stat = os.fstat(f.fileno())
            print('  -> fsize', stat.st_size)
            if othername is None:
                othername = file
            fsize = struct.pack('>q', stat.st_size)

            self.cmd(b'sf'+self.sstr(othername)+fsize)

            status = self.channel.recv(3)
            if status!=b'OK\n':
                print('Something went wrong...')
                exit(1)

            i = stat.st_size
            while i>0:
                fdata = f.read(1024)
                i -= 1024
                self.channel.sendall(fdata)

    def recv_file(self, file):
        print(f"< {file}")
        if os.path.dirname(file) != '':
            os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'wb') as f:
            self.cmd(b'rf'+self.sstr(file))
            status = self.channel.recv(2)
            if status!=b'OK':
                msg = self.channel.recv(1024)
                print("Error:", bytes.decode(msg, 'ascii'))
                exit(1)
            fsize = self.channel.recv(8)
            fsize = struct.unpack('>q', fsize)[0]
            print('  -> fsize', fsize)
            while fsize>0:
                f.write(self.channel.recv(1024))
                fsize -= 1024

    def do_ip_gen(self, target):
        print("+ Generate IPs")
        self.send_file(self.configfile, 'project.cfg')
        self.heartbeat.printing = True
        self.cmd(b'do'+self.sstr(f'ip {target}'))
        res = struct.unpack('>I', self.channel.recv(4))[0]
        self.heartbeat.printing = False
        print(f' [{res}]')

        # get used IP's for target
        ips = self.config.get(target, 'src_ip', fallback='').split()
        for i, ip in enumerate(ips):
            self.recv_dir(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{ip}")

        if res != 0:
            print("Some error occured...")
            exit(1)

    def do_synthesize(self, target):
        print("+ Synthesize")

        self.send_file(self.configfile, 'project.cfg')
        src = self.config.get(target, 'src_vhdl', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_verilog', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_sysverilog', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_ip', fallback='').split()
        for s in src:
            if self.tc=='ISE':
                self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{s}/{s}.vhd")
            elif self.tc=="VIVADO":
                self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{s}/{s}.xci")
        if self.tc=="VIVADO":
            self.send_file(f"{self.config.get(target, 'src_constraints', fallback='__con__')}")

        self.heartbeat.printing = True
        self.cmd(b'do'+self.sstr(f'syn {target}'))
        res = struct.unpack('>I', self.channel.recv(4))[0]
        self.heartbeat.printing = False
        print(f' [{res}]')

        if res != 0:
            print("Some error occured...")
            if self.tc=='ISE':
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/syn.log")
            elif self.tc=="VIVADO":
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/synth.log")
            exit(1)

        if self.tc=='ISE':
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.ngc")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.v")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/syn.log")
        elif self.tc=="VIVADO":
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/synth.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/post_synth.dcp")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/synth_netlist.v")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/synth_netlist.sdf")

    def do_implement(self, target):
        print("+ Implement")

        self.send_file(self.configfile, 'project.cfg')
        if self.tc=='ISE':
            self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.ngc")
            self.send_file(f"{self.config.get(target, 'src_constraints', fallback='__con__')}")
        elif self.tc=="VIVADO":
            self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/post_synth.dcp")

        self.heartbeat.printing = True
        self.cmd(b'do'+self.sstr(f'impl {target}'))
        res = struct.unpack('>I', self.channel.recv(4))[0]
        self.heartbeat.printing = False
        print(f' [{res}]')

        if res != 0:
            print("Some error occured...")
            if self.tc=='ISE':
                # FIXME possible that not all are there
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-ngd.log")
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-map.log")
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-par.log")
            elif self.tc=="VIVADO":
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl.log")
            exit(1)

        if self.tc=='ISE':
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-ngd.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-map.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl-par.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.map.v")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.map.sdf")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.ncd")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.pcf")
        elif self.tc=="VIVADO":
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/post_impl.dcp")

    def do_bit(self, target):
        print("+ Generate output files")

        self.send_file(self.configfile, 'project.cfg')
        if self.tc=='ISE':
            self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.ncd")
            self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.pcf")
        elif self.tc=="VIVADO":
            self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/post_impl.dcp")

        self.heartbeat.printing = True
        self.cmd(b'do'+self.sstr(f'bit {target}'))
        res = struct.unpack('>I', self.channel.recv(4))[0]
        self.heartbeat.printing = False
        print(f' [{res}]')

        if res != 0:
            print("Some error occured...")
            if self.tc=='ISE':
                # TODO what to send?
                pass
            elif self.tc=="VIVADO":
                self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/bit.log")
            exit(1)

        if self.tc=='ISE':
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/timing.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.bit")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{target}.bin")
        elif self.tc=="VIVADO":
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/bit.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/out.bit")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/out.bin")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/power.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/timing.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/util.log")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/system.xsa")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/total.dcp")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl_netlist.sdf")
            self.recv_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/impl_netlist.v")

    def do_floorplan(self, target):
        print("Error: floorplan editing not implemented for remote execution")
        exit(1)

    def do_sim(self, target):
        print("+ Simulate")

        self.send_file(self.configfile, 'project.cfg')

        src = self.config.get(target, 'src_vhdl', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_verilog', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_sysverilog', fallback='').split()
        for s in src:
            self.send_file(s)
        src = self.config.get(target, 'src_sdf', fallback='')
        if src!='':
            self.send_file(src)
        src = self.config.get(target, 'src_ip', fallback='').split()
        for s in src:
            if self.tc=='ISE':
                self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{s}/{s}.vhd")
            elif self.tc=="VIVADO":
                self.send_file(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}/{s}/{s}.xci")
        if self.tc=="VIVADO":
            src = self.config.get(target, 'src_c', fallback='').split()
            for s in src:
                self.send_file(s)

        self.heartbeat.printing = True
        self.cmd(b'do'+self.sstr(f'sim {target}'))
        res = struct.unpack('>I', self.channel.recv(4))[0]
        self.heartbeat.printing = False
        print(f' [{res}]')

        self.recv_dir(f"{self.config.get('project', 'out_dir', fallback='OUT')}/{target}")