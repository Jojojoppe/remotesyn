import os
import shutil
import subprocess
import time

class exec_ISE:
    def __init__(self, config, builddir):
        self.config = config
        self.builddir = builddir
        self.create_builddir()

    def create_outdir(self, target):
        self.outdir = self.config.get('project', 'out_dir', fallback='OUT')
        if not os.path.exists(self.outdir):
            os.mkdir(self.outdir)
        if not os.path.exists(f'{self.outdir}/{target}'):
            os.mkdir(f'{self.outdir}/{target}')

    def create_builddir(self):
        if not os.path.exists(self.builddir):
            os.mkdir(self.builddir)

    def enter_builddir(self):
        self.curdir = os.getcwd()
        os.chdir(self.builddir)

    def leave_builddir(self):
        os.chdir(self.curdir)

    def do_ip_gen(self, target):
        # get used IP's for target
        ips = self.config.get(target, 'src_ip', fallback='').split()
        self.create_outdir(target)

        print("+ Generate IPs")

        for i, ip in enumerate(ips):
            # Create cgp file
            with open(f'{self.builddir}/coregen_{i}.cgp', 'w') as f:
                f.write(f'SET busformat = BusFormatAngleBracketNotRipped\n')
                f.write(f'SET designentry = VHDL\n')
                f.write(f'SET device = {self.config.get("target", "device")}\n')
                f.write(f'SET devicefamily = {self.config.get("target", "family")}\n')
                f.write(f'SET package = {self.config.get("target", "package")}\n')
                f.write(f'SET speedgrade = {self.config.get("target", "speedgrade")}\n')
                f.write(f'SET flowvendor = Other\n')
                f.write(f'SET verilogsim = true\n')
                f.write(f'SET vhdlsim = true\n')
            # crete xco file
            with open(f'{self.builddir}/coregen_{i}.xco', 'w') as f:
                ipsec = 'ip_%s'%ip
                f.write(f'SELECT {ip} {self.config.get(ipsec, ipsec)}\n')
                for s in self.config[ipsec]:
                    if s==ipsec:
                        continue
                    f.write(f'CSET {s}={self.config.get(ipsec, s)}\n')
                f.write('GENERATE')
            # Clear log
            if os.path.exists(f'{self.builddir}/coregen.log'):
                os.remove(f'{self.builddir}/coregen.log')
            # Run coregen
            pid = subprocess.Popen(f'coregen -p coregen_{i}.cgp -b coregen_{i}.xco', shell=True, cwd=self.builddir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            while pid.poll() is None:
                print('.', end='', flush=True)
                time.sleep(2)
            res = pid.returncode
            print('')

            if not os.path.exists(f'{self.outdir}/{target}/{ip}'):
                os.mkdir(f'{self.outdir}/{target}/{ip}')
            # Copy files to output directory if succeeded
            if res == 0:
                shutil.copyfile(f'{self.builddir}/{ip}.vhd', f'{self.outdir}/{target}/{ip}/{ip}.vhd')
                shutil.copyfile(f'{self.builddir}/{ip}.v', f'{self.outdir}/{target}/{ip}/{ip}.v')
                shutil.copyfile(f'{self.builddir}/{ip}.ngc', f'{self.outdir}/{target}/{ip}/{ip}.ngc')
            # Copy log
            shutil.copyfile(f'{self.builddir}/coregen.log', f'{self.outdir}/{target}/{ip}/{ip}.log')
            
            if res!=0:
                exit(res)

    def do_synthesize(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Synthesize')

        extra_opts = self.config.get(target, 'extra_options').split('\n')
        opts = {}
        for o in extra_opts:
            tp = o.split()[0]
            op = ' '.join(o.split()[1:])
            opts[tp] = op

        if 'xst' not in opts:
            opts['xst'] = ''

        if 'netgen' not in opts:
            opts['netgen'] = ''
 
        with open('syn.prj', 'w') as f:
            src = self.config.get(target, 'src_vhdl', fallback='').split()
            for s in src:
                f.write(f'vhdl work "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_verilog', fallback='').split()
            for s in src:
                f.write(f'verilog work "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_sysverilog', fallback='').split()
            for s in src:
                f.write(f'verilog work "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_ip', fallback='').split()
            for s in src:
                f.write(f'vhdl work "{self.curdir}/{self.outdir}/{target}/{s}/{s}.vhd"\n')
        with open('prj.scr', 'w') as f:
            f.write('run\n-ifn syn.prj\n-ofn syn.ngc\n-ifmt mixed\n')
            f.write(f"-top {self.config.get(target, 'toplevel', fallback='_top_')}\n")
            f.write(f"-p {self.config.get('target', 'device', fallback='_d_')}")
            f.write(self.config.get('target', 'speedgrade', fallback='_s_'))
            f.write(f"-{self.config.get('target', 'package', fallback='_p_')}")
            f.write(f"\n{opts['xst']}\n")

        pid = subprocess.Popen(f'xst -intstyle xflow -ifn prj.scr', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        if res!=0:
            self.leave_builddir()
            exit(res)

        success = True
        pid = subprocess.Popen(f"netgen -intstyle xflow -sim -ofmt verilog -w -insert_glbl true {opts['netgen']} syn.ngc", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        if res!=0:
            success = False
            exit(res)

        self.leave_builddir()

        if success:
            if not os.path.exists(f'{self.outdir}/{target}'):
                os.mkdir(f'{self.outdir}/{target}')
            # Copy files to output directory if succeeded
            shutil.copyfile(f'{self.builddir}/syn.ngc', f'{self.outdir}/{target}/{target}.ngc')
            shutil.copyfile(f'{self.builddir}/syn.v', f'{self.outdir}/{target}/{target}.v')
        shutil.copyfile(f'{self.builddir}/prj.srp', f'{self.outdir}/{target}/syn.log')
        
    def do_implement(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Implement')

        extra_opts = self.config.get(target, 'extra_options').split('\n')
        opts = {}
        for o in extra_opts:
            tp = o.split()[0]
            op = ' '.join(o.split()[1:])
            opts[tp] = op

        if 'ngd' not in opts:
            opts['ngd'] = ''

        if 'map' not in opts:
            opts['map'] = ''

        if 'par' not in opts:
            opts['par'] = ''

        part = f"{self.config.get('target', 'device', fallback='_d_')}{self.config.get('target', 'speedgrade', fallback='_s_')}-{self.config.get('target', 'package', fallback='_p_')}"
        cons = self.config.get(target, 'src_constraints', fallback='__con__')
        pid = subprocess.Popen(f"ngdbuild -intstyle xflow -p {part} -uc {self.curdir}/{cons} {opts['ngd']} {self.curdir}/{self.outdir}/{target}/{target}.ngc impl.ngd", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        shutil.copyfile(f'impl.bld', f'{self.curdir}/{self.outdir}/{target}/impl-ngd.log')
        if res!=0:
            self.leave_builddir()
            exit(res)

        pid = subprocess.Popen(f"map -intstyle xflow -detail -p {part} {opts['map']} -w impl.ngd -o impl.map.ncd impl.pcf", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        shutil.copyfile(f'impl.map.mrp', f'{self.curdir}/{self.outdir}/{target}/impl-map.log')
        if res!=0:
            self.leave_builddir()
            exit(res)

        pid = subprocess.Popen(f"par -intstyle xflow {opts['par']} -w impl.map.ncd impl.pcf | tee impl.par.log", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        shutil.copyfile(f'impl.par.log', f'{self.curdir}/{self.outdir}/{target}/impl-par.log')
        if res!=0:
            self.leave_builddir()
            exit(res)

        pid = subprocess.Popen(f"netgen -intstyle xflow -sim -ofmt verilog -w -insert_glbl true -sdf_anno true {opts['netgen']} impl.map.ncd", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        if res!=0:
            self.leave_builddir()
            exit(res)

        self.leave_builddir()

        shutil.copyfile(f'{self.builddir}/impl.map.v', f'{self.outdir}/{target}/{target}.map.v')
        shutil.copyfile(f'{self.builddir}/impl.map.sdf', f'{self.outdir}/{target}/{target}.map.sdf')
        shutil.copyfile(f'{self.builddir}/impl.pcf.ncd', f'{self.outdir}/{target}/{target}.ncd')
        shutil.copyfile(f'{self.builddir}/impl.pcf', f'{self.outdir}/{target}/{target}.pcf')

    def do_bit(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Generate output files')

        extra_opts = self.config.get(target, 'extra_options').split('\n')
        opts = {}
        for o in extra_opts:
            tp = o.split()[0]
            op = ' '.join(o.split()[1:])
            opts[tp] = op

        if 'bitgen' not in opts:
            opts['bitgen'] = ''

        if 'trce' not in opts:
            opts['trce'] = ''

        pid = subprocess.Popen(f"bitgen -intstyle xflow -g Binary:Yes -w {opts['bitgen']} {self.curdir}/{self.outdir}/{target}/{target}.ncd bit.bit {self.curdir}/{self.outdir}/{target}/{target}.pcf", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        self.leave_builddir()
        shutil.copyfile(f'{self.builddir}/bit.bit', f'{self.outdir}/{target}/{target}.bit')
        shutil.copyfile(f'{self.builddir}/bit.bin', f'{self.outdir}/{target}/{target}.bin')
        if res!=0:
            exit(res)

        self.enter_builddir()
        pid = subprocess.Popen(f"trce -intstyle xflow {opts['trce']} {self.curdir}/{self.outdir}/{target}/{target}.ncd {self.curdir}/{self.outdir}/{target}/{target}.pcf", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        self.leave_builddir()
        shutil.copyfile(f'{self.builddir}/{target}.twr', f'{self.outdir}/{target}/timing.log')
        if res!=0:
            exit(res)

    def do_floorplan(self, target):
        self.create_outdir(target)
        self.enter_builddir()
        part = f"{self.config.get('target', 'device', fallback='_d_')}{self.config.get('target', 'package', fallback='_p_')}{self.config.get('target', 'speedgrade', fallback='_s_')}"
        cons = f"{self.curdir}/{self.config.get(target, 'src_constraints', fallback='__con__')}"
        with open('paproj.tcl', 'w') as f:
            f.write(f'create_project -name paproj -dir paproj -part {part} -force\n')
            f.write('set_property design_mode GateLvl [get_property srcset [current_run -impl]]\n')
            f.write(f"set_property edif_top_file {self.curdir}/{self.outdir}/{target}/{target}.ngc [get_property srcset [current_run]]\n")
            f.write(f"add_files [list {{{cons}}}] -fileset [get_property constrset [current_run]]\n")
            f.write(f"set_property target_constrs_file {cons} [current_fileset -constrset]\n")
            f.write(f"link_design\nread_xdl -file {self.curdir}/{self.outdir}/{target}/{target}.ncd\n")
        pid = subprocess.Popen('planAhead -source paproj.tcl', shell=True) #, stdout=subprocess.DEVNULL, stderr=None)
        res = pid.wait()
        self.leave_builddir()

    def do_sim(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Simulate')

        if os.path.exists('isim'):
            shutil.rmtree('isim')

        with open('sim.prj', 'w') as f:
            src = self.config.get(target, 'src_vhdl', fallback='').split()
            for s in src:
                f.write(f'vhdl work "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_verilog', fallback='').split()
            for s in src:
                f.write(f'verilog work "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_sysverilog', fallback='').split()
            for s in src:
                f.write(f'verilog work "{self.curdir}/{s}"\n')
            # TODO add IP

        extras = ''
        if self.config.get(target, 'simtype', fallback='presim') == 'postsim':
            extras = f"--{self.config.get(target, 'delay', fallback='typ')}delay work.glbl"

        pid = subprocess.Popen(f"fuse {extras} work.{self.config.get(target, 'toplevel', fallback='toplevel')} -prj sim.prj -o sim", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        if res!=0:
            self.leave_builddir()
            shutil.copyfile(f'{self.builddir}/fuse.log', f'{self.outdir}/{target}/synth.log')
            exit(res)

        with open('sim.tcl', 'w') as f:
            f.write("onerror {resume}\n")
            f.write("vcd dumpfile sim.vcd\n")
            f.write(f"vcd dumpvars -m {self.config.get(target, 'toplevel', fallback='toplevel')} -l {self.config.get(target, 'levels', fallback='10')}\n")
            f.write("vcd dumpon\n")
            f.write(f"run {self.config.get(target, 'runtime', fallback='100 ns')}\n")
            f.write("vcd dumpflush\nquit\n")
        
        extras = ''
        if self.config.get(target, 'simtype', fallback='presim') == 'postsim':
            extras = f"-sdf{self.config.get(target, 'delay', fallback='typ')} {self.config.get(target, 'sdfroot', fallback='dut')}={self.curdir}/{self.config.get(target, 'src_sdf', fallback='_s_')}"

        pid = subprocess.Popen(f'./sim -tclbatch sim.tcl {extras} > sim.log', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        res = pid.returncode
        print('')
        if res!=0:
            exit(res)

        self.leave_builddir()

        if not os.path.exists(f'{self.outdir}/{target}'):
            os.mkdir(f'{self.outdir}/{target}')
        shutil.copyfile(f'{self.builddir}/sim.vcd', f'{self.outdir}/{target}/output.vcd')
        shutil.copyfile(f'{self.builddir}/fuse.log', f'{self.outdir}/{target}/synth.log')
        shutil.copyfile(f'{self.builddir}/sim.log', f'{self.outdir}/{target}/output.log')