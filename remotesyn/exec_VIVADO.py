import os
import shutil
import subprocess
import time
import glob

class exec_VIVADO:
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

        dev = self.config.get('target', 'device', fallback='_d_')
        sgrade = self.config.get('target', 'speedgrade', fallback='_s_')
        pkg = self.config.get('target', 'package', fallback='_p_')

        for i, ip in enumerate(ips):
            self.enter_builddir()
            ipsec = 'ip_%s'%ip
            ipname = self.config.get(ipsec, ipsec)

            ipconfig = '[ list \\\n'
            for s in self.config[ipsec]:
                if s==ipsec:
                    continue
                ipconfig += f'    CONFIG.{s.upper()} {{{self.config.get(ipsec, s)}}}\\\n'
            ipconfig += '  ]'

            with open('do.tcl', 'w') as f:
                f.write(f"file mkdir {ip}\ncreate_project -in_memory\nset_property part {dev}{pkg}{sgrade} [current_project]\n")
                f.write(f"create_ip -name {ipname.split(':')[2]} -vendor {ipname.split(':')[1]} -library {ipname.split(':')[0 ]} -module_name {ip} -dir {ip}\n")
                f.write(f"set_property -dict {ipconfig} [ get_ips {ip} ]\n")
                f.write(f"export_ip_user_files -of_objects [get_files {ip}/{ip}/{ip}.xci ] -no_script -sync -force -quiet\n")
                f.write(f"upgrade_ip [get_ips]\ngenerate_target all [get_ips]\n#synth_ip [get_ips]\n")
                # f.write(f"export_simulation -directory {ip} -simulator xsim -absolute_path -export_source_files -of_objects [get_files {ip}/{ip}/{ip}.xci]")

            pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            while pid.poll() is None:
                print('.', end='', flush=True)
                time.sleep(2)
            ret = pid.returncode
            print('')

            if ret != 0:
                self.leave_builddir()
                if not os.path.exists(f'{self.outdir}/{target}/{ip}'):
                    os.mkdir(f'{self.outdir}/{target}/{ip}')
                shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/{ip}/log.log')
                exit(ret)

            self.leave_builddir()
            if not os.path.exists(f'{self.outdir}/{target}/{ip}'):
                os.mkdir(f'{self.outdir}/{target}/{ip}')
            shutil.copyfile(f"{self.builddir}/{ip}/{ip}/{ip}.vho", f'{self.outdir}/{target}/{ip}/{ip}.vho')
            shutil.copyfile(f"{self.builddir}/{ip}/{ip}/{ip}.veo", f'{self.outdir}/{target}/{ip}/{ip}.veo')
            shutil.copyfile(f"{self.builddir}/{ip}/{ip}/{ip}.xci", f'{self.outdir}/{target}/{ip}/{ip}.xci')
            shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/{ip}/log.log')

            for f in glob.glob(f"{self.builddir}/{ip}/{ip}/*.c"):
                shutil.copy(f, f'{self.outdir}/{target}/{ip}/')
            for f in glob.glob(f"{self.builddir}/{ip}/{ip}/*.h"):
                shutil.copy(f, f'{self.outdir}/{target}/{ip}/')

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

        if 'syn' not in opts:
            opts['syn'] = ''

        if 'netlist_top' not in opts:
            opts['netlist_top'] = self.config.get(target, 'toplevel', fallback='toplevel')

        dev = self.config.get('target', 'device', fallback='_d_')
        sgrade = self.config.get('target', 'speedgrade', fallback='_s_')
        pkg = self.config.get('target', 'package', fallback='_p_')

        with open('do.tcl', 'w') as f:
            src = self.config.get(target, 'src_vhdl', fallback='').split()
            for s in src:
                f.write(f'read_vhdl "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_verilog', fallback='').split()
            for s in src:
                f.write(f'read_verilog "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_sysverilog', fallback='').split()
            for s in src:
                f.write(f'read_verilog -sv "{self.curdir}/{s}"\n')
            src = self.config.get(target, 'src_constraints', fallback='')
            f.write(f'read_xdc "{self.curdir}/{src}"\n')
            src = self.config.get(target, 'src_ip', fallback='').split()
            for s in src:
                if os.path.exists(s):
                    shutil.rmtree(s)
                os.mkdir(s)
                shutil.copyfile(f'{self.curdir}/{self.outdir}/{target}/{s}/{s}.xci', f'{s}/{s}.xci')
                f.write(f'read_ip "{s}/{s}.xci"\n')

            f.write(f"set_property part {dev}{pkg}{sgrade} [current_project]\n")
            f.write(f"upgrade_ip [get_ips]\ngenerate_target all [get_ips]\nsynth_ip [get_ips]\n")
            f.write(f"synth_design -top {self.config.get(target, 'toplevel', fallback='toplevel')} -part {dev}{pkg}{sgrade} {opts['syn']}\n")

            f.write(f"write_checkpoint -force post_synth.dcp\nwrite_verilog -force -mode timesim -cell {opts['netlist_top']} -sdf_anno true -nolib netlist.v\n")
            f.write(f"write_sdf -force -cell {opts['netlist_top']} -mode timesim netlist.sdf\n")

        pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')

        if ret != 0:
            self.leave_builddir()
            shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/synth.log')
            exit(ret)

        self.leave_builddir()
        shutil.copyfile(f'{self.builddir}/netlist.v', f'{self.outdir}/{target}/synth_netlist.v')
        shutil.copyfile(f'{self.builddir}/netlist.sdf', f'{self.outdir}/{target}/synth_netlist.sdf')
        shutil.copyfile(f'{self.builddir}/post_synth.dcp', f'{self.outdir}/{target}/post_synth.dcp')
        shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/synth.log')

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

        if 'opt' not in opts:
            opts['opt'] = ''
        if 'place' not in opts:
            opts['place'] = ''
        if 'route' not in opts:
            opts['route'] = ''

        with open('do.tcl', 'w') as f:
            f.write(f"open_checkpoint {self.curdir}/{self.outdir}/{target}/post_synth.dcp\n")
            f.write(f"opt_design {opts['opt']}\nplace_design {opts['place']}\nroute_design {opts['route']}\n")
            f.write(f"write_checkpoint -force {self.curdir}/{self.outdir}/{target}/post_impl.dcp\n")

        pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')

        if ret != 0:
            self.leave_builddir()
            shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/impl.log')
            exit(ret)

        self.leave_builddir()
        shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/impl.log')

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

        if 'netlist_top' not in opts:
            opts['netlist_top'] = self.config.get(target, 'toplevel', fallback='toplevel')

        with open('do.tcl', 'w') as f:
            f.write(f"open_checkpoint {self.curdir}/{self.outdir}/{target}/post_impl.dcp\n")
            f.write(f"set_property SEVERITY {{Warning}} [get_drc_checks NSTD-1]\nset_property SEVERITY {{Warning}} [get_drc_checks UCIO-1]\n")
            f.write(f"set_property BITSTREAM.General.UnconstrainedPins {{Allow}} [current_design]\n")
            f.write(f"write_debug_probes -force out.ltx\nwrite_bitstream -force -bin_file out.bit\nreport_timing_summary -file timing.log\nreport_power -file power.log\n")
            f.write(f"report_utilization -file util.log\n")
            f.write(f"write_checkpoint -force {self.curdir}/{self.outdir}/{target}/total.dcp\n")
            f.write(f"open_checkpoint {self.curdir}/{self.outdir}/{target}/total.dcp\n")
            f.write(f"write_hw_platform -fixed -force -file {self.curdir}/{self.outdir}/{target}/system.xsa\n")
            f.write(f"write_verilog -force -mode timesim -cell {opts['netlist_top']} -rename_top {opts['netlist_top']} -sdf_anno true netlist.v\n") # -nolib
            f.write(f"write_sdf -force -cell {opts['netlist_top']} -rename_top {opts['netlist_top']} -mode timesim netlist.sdf\n")

        pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')

        if ret != 0:
            self.leave_builddir()
            shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/bit.log')
            exit(ret)

        self.leave_builddir()

        shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/bit.log')
        shutil.copyfile(f"{self.builddir}/timing.log", f'{self.outdir}/{target}/timing.log')
        shutil.copyfile(f"{self.builddir}/util.log", f'{self.outdir}/{target}/util.log')
        shutil.copyfile(f"{self.builddir}/power.log", f'{self.outdir}/{target}/power.log')
        shutil.copyfile(f"{self.builddir}/out.bit", f'{self.outdir}/{target}/out.bit')
        shutil.copyfile(f"{self.builddir}/out.bin", f'{self.outdir}/{target}/out.bin')
        shutil.copyfile(f"{self.builddir}/netlist.v", f'{self.outdir}/{target}/impl_netlist.v')
        shutil.copyfile(f"{self.builddir}/netlist.sdf", f'{self.outdir}/{target}/impl_netlist.sdf')

    def do_floorplan(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Open floorplan viewer')

        with open('do.tcl', 'w') as f:
            f.write(f"open_checkpoint {self.curdir}/{self.outdir}/{target}/post_impl.dcp\n")
            f.write(f"start_gui")

        pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')

        self.leave_builddir()

        if ret != 0:
            exit(ret)

    def do_sim(self, target):
        self.create_outdir(target)
        self.enter_builddir()

        print('+ Simulate')

        if os.path.exists('sim'):
            shutil.rmtree('sim')

        dev = self.config.get('target', 'device', fallback='_d_')
        sgrade = self.config.get('target', 'speedgrade', fallback='_s_')
        pkg = self.config.get('target', 'package', fallback='_p_')

        with open('do.tcl', 'w') as f:
            f.write(f"create_project -force -part {dev}{pkg}{sgrade} sim sim\n")
            src = self.config.get(target, 'src_vhdl', fallback='').split()
            for s in src:
                f.write(f'add_files -norecurse -scan_for_includes {self.curdir}/{s}\n')
                f.write(f'import_files -norecurse {self.curdir}/{s}\n')
            src = self.config.get(target, 'src_verilog', fallback='').split()
            for s in src:
                f.write(f'add_files -norecurse -scan_for_includes {self.curdir}/{s}\n')
                f.write(f'import_files -norecurse {self.curdir}/{s}\n')
            src = self.config.get(target, 'src_sysverilog', fallback='').split()
            for s in src:
                f.write(f'add_files -norecurse -scan_for_includes {self.curdir}/{s}\n')
                f.write(f'import_files -norecurse {self.curdir}/{s}\n')
            src = self.config.get(target, 'src_ip', fallback='').split()
            for s in src:
                f.write(f'add_files -norecurse {self.curdir}/{self.outdir}/{s}/{s}.xci\n')
            src = self.config.get(target, 'src_c', fallback='').split()
            for s in src:
                if s.endswith('.h'):
                    continue
                f.write(f'add_files -norecurse -scan_for_includes {self.curdir}/{s}\n')
                f.write(f'import_files -norecurse {self.curdir}/{s}\n')

            if self.config.get(target, 'src_sdf', fallback='__sdf__') != '__sdf__':
                s = self.config.get(target, 'src_sdf', fallback='__sdf__')
                f.write(f'add_files -norecurse -scan_for_includes {self.curdir}/{s}\n')
                f.write(f'import_files -norecurse {self.curdir}/{s}\n')
                f.write(f"file mkdir sim/sim.sim/sim_1/behav/xsim\nfile copy -force {self.curdir}/{s} {self.curdir}/{self.builddir}/sim/sim.sim/sim_1/behav/xsim/netlist.sdf\n")
                # f.write(f"file mkdir sim/sim.sim/sim_1/behav/xsim\nfile copy -force {self.curdir}/{s} {self.curdir}/{self.builddir}/sim/sim.sim/sim_1/behav/xsim/{os.path.split(s)[1]}\n")

            f.write(f"set_property top {self.config.get(target, 'toplevel', fallback='toplevel')} [get_filesets sim_1]\n")
            f.write("set_property top_lib xil_defaultlib [get_filesets sim_1]\n")
            f.write("launch_simulation -noclean_dir -scripts_only -absolute_path\n")

        pid = subprocess.Popen('vivado -mode batch -source do.tcl', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')

        if ret != 0:
            self.leave_builddir()
            print("Something went wrong...")
            shutil.copyfile(f"{self.builddir}/vivado.log", f'{self.outdir}/{target}/prepare.log')
            exit(ret)

        shutil.copyfile(f"vivado.log", f'{self.curdir}/{self.outdir}/{target}/prepare.log')

        extras = ''
        if self.config.get(target, 'simtype', fallback='presim') == 'postsim':
            extras = f"-{self.config.get(target, 'delay', fallback='typ')}delay -transport_int_delays -pulse_r 0 -pulse_int_r 0 -L simprims_ver"

        pid = subprocess.Popen(f'sed -i "s/xelab/xelab {extras}/g" elaborate.sh', shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')
        if ret!=0:
            print("Something went wrong with editing elaborate stage...")
            exit(ret)

        if self.config.get(target, 'simtype', fallback='presim') == 'postsim':
            pid = subprocess.Popen(f"sed -i '/ \/I /d' netlist.sdf && sed -i '/glbl.v/d' *.prj", shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # pid = subprocess.Popen(f"sed -i '/glbl.v/d' *.prj", shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            while pid.poll() is None:
                print('.', end='', flush=True)
                time.sleep(2)
            ret = pid.returncode
            print('')
            if ret!=0:
                print("Something went wrong with editing project files...")
                exit(ret)

        pid = subprocess.Popen(f'bash compile.sh', shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')
        if ret!=0:
            self.leave_builddir()
            print("Compile error")
            shutil.copyfile(f"{self.builddir}/sim/sim.sim/sim_1/behav/xsim/compile.log", f'{self.outdir}/{target}/compile.log')
            exit(ret)
        shutil.copyfile(f"{self.curdir}/{self.builddir}/sim/sim.sim/sim_1/behav/xsim/compile.log", f'{self.curdir}/{self.outdir}/{target}/compile.log')

        pid = subprocess.Popen(f'bash elaborate.sh', shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')
        if ret!=0:
            self.leave_builddir()
            print("Elaborate error")
            shutil.copyfile(f"{self.builddir}/sim/sim.sim/sim_1/behav/xsim/elaborate.log", f'{self.outdir}/{target}/elaborate.log')
            exit(ret)
        shutil.copyfile(f"{self.curdir}/{self.builddir}/sim/sim.sim/sim_1/behav/xsim/elaborate.log", f'{self.curdir}/{self.outdir}/{target}/elaborate.log')

        with open(f"sim/sim.sim/sim_1/behav/xsim/{self.config.get(target, 'toplevel', fallback='toplevel')}.tcl", 'w') as f:
            f.write(f"open_vcd out.vcd\nlog_vcd\nrun {self.config.get(target, 'runtime', fallback='100 ns')}\nclose_vcd\nquit\n")

        pid = subprocess.Popen(f'bash simulate.sh', shell=True, cwd='sim/sim.sim/sim_1/behav/xsim', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while pid.poll() is None:
            print('.', end='', flush=True)
            time.sleep(2)
        ret = pid.returncode
        print('')
        if ret!=0:
            self.leave_builddir()
            print("Simulation error")
            shutil.copyfile(f"{self.builddir}/sim/sim.sim/sim_1/behav/xsim/simulate.log", f'{self.outdir}/{target}/simulate.log')
            exit(ret)
        shutil.copyfile(f"{self.curdir}/{self.builddir}/sim/sim.sim/sim_1/behav/xsim/simulate.log", f'{self.curdir}/{self.outdir}/{target}/simulate.log')

        self.leave_builddir()
        shutil.copyfile(f'{self.builddir}/sim/sim.sim/sim_1/behav/xsim/out.vcd', f'{self.outdir}/{target}/output.vcd')