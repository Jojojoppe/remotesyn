import threading
import shutil
import os
import time
import subprocess
import signal
import random

from .runner import runner

class synth(threading.Thread):
    def __init__(self, config, copy, target):
        threading.Thread.__init__(self)
        self.config = config
        self.copy = copy
        self.target = target

        self.threads = []
        self.running = True
        self.name = config.get('project', 'name', fallback=f'{random.random():.4f}')
        self.version = config.get('project', 'version', fallback=f'{random.random():.4f}')
        self.builddir = f"{config.get('project', 'build_dir', fallback='.build')}/synth_{target}_{self.name}_{self.version}"
        self.outdir = config.get('project', 'out_dir', fallback='out')

    # Returns the list of needed files to execute operation. Caller need
    # to check for existance of the files and if in remote execution these
    # files must be synched
    def needed_files(self):
        if not self.config.has_section(f'sources:{self.target}'):
            print("ERROR: config file has no sources section for target")
            return None
        needed_files = []
        for s in self.config.get(f'sources:{self.target}', 'src_vhdl', fallback="").split():
            needed_files.append(s)
        for s in self.config.get(f'sources:{self.target}', 'src_verilog', fallback="").split():
            needed_files.append(s)
        for s in self.config.get(f'sources:{self.target}', 'src_sysverilog', fallback="").split():
            needed_files.append(s)
        return needed_files
    
    def stop(self):
        print("Stopping synth...")
        for t in self.threads:
            print(" <> kill", t)
            t.send_signal(signal.SIGINT)
            ti = 0
            while t.poll() is None:
                time.sleep(1)
                ti += 1
                if ti>2:
                    print(" <> force kill", t)
                    t.send_signal(signal.SIGKILL)
        self.running = False

    def run(self):
        print("Synthesize:")
        if not self.config.has_section(f'sources:{self.target}'):
            print("ERROR: config file has no sources section for target")
            self.running = False
            return None

        devtarget = f'target:{self.config.get(f"sources:{self.target}", "target", fallback="")}'
        if not self.config.has_section(devtarget):
            print("ERROR: config file has no section for device target")
            self.running = False
            return None

        device = f"{self.config.get(devtarget, 'device', fallback='')}{self.config.get(devtarget, 'speedgrade', fallback='')}-{self.config.get(devtarget, 'package', fallback='')}"

        os.makedirs(self.builddir, exist_ok=True)
        curdir = os.getcwd()
        os.chdir(self.builddir)

        try:

            print(" - writing project file")
            with open('syn.prj', 'w') as f:
                for s in self.config.get(f'sources:{self.target}', 'src_vhdl', fallback="").split():
                    f.write(f"vhdl work {curdir}/{s}\n")
                for s in self.config.get(f'sources:{self.target}', 'src_verilog', fallback="").split():
                    f.write(f"verilog work {curdir}/{s}\n")
                for s in self.config.get(f'sources:{self.target}', 'src_sysverilog', fallback="").split():
                    f.write(f"verilog work {curdir}/{s}\n")

            print(" - writing project generation file")
            with open('prj.scr', 'w') as f:
                f.write(f'run\n-ifn syn.prj\n-ofn syn.ngc\n-ifmt mixed\n')
                f.write(f'-top {self.config.get(f"sources:{self.target}", "toplevel", fallback="toplevel")}\n')
                f.write(f'-p {device}\n-glob_opt max_delay -opt_mode speed')

            runner(self.threads, "xst -intstyle xflow -ifn prj.scr", "xst")
            if not self.running:
                os.chdir(curdir)
                return
            print('DONE')

            print(" - copy output files")
            os.makedirs(f'{curdir}/{self.outdir}/{self.target}', exist_ok=True)
            self.copy.copy_to_dir('syn.ngc', f'{curdir}/{self.outdir}/{self.target}/synth.ngc')
            self.copy.copy_to_dir('prj.srp', f'{curdir}/{self.outdir}/{self.target}/synth.log')

        except Exception as e:
            print(e)

        finally:
            os.chdir(curdir)
            self.running = False