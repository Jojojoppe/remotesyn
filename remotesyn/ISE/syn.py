import threading
import shutil
import os
import time
import subprocess
import signal
import random

def needed_files(config, target) -> list:
    if not config.has_section(f'build:{target}'):
        print("ERROR: config file has no build section for target")
        return None
    needed_files = []
    for s in config.get(f'build:{target}', 'src_vhdl', fallback="").split():
        needed_files.append(s)
    for s in config.get(f'build:{target}', 'src_verilog', fallback="").split():
        needed_files.append(s)
    for s in config.get(f'build:{target}', 'src_sysverilog', fallback="").split():
        needed_files.append(s)
    return needed_files

def generated_files(config, target) -> list:
    outdir = f"{config.get('project', 'out_dir', fallback='out')}"
    return [
        f'{outdir}/{target}/synth.log',
        f'{outdir}/{target}/synth.ngc',
    ]

def do(config, target, log, subprocesses, prefix='.') -> int:
    log("Synthesize:")

    if not config.has_section(f'build:{target}'):
        log("ERROR: config file has no build section for target")
        return 1

    devtarget = f'target:{config.get(f"build:{target}", "target", fallback="")}'
    if not config.has_section(devtarget):
        log("ERROR: config file has no section for device target")
        return 1

    device = f"{config.get(devtarget, 'device', fallback='')}{config.get(devtarget, 'speedgrade', fallback='')}-{config.get(devtarget, 'package', fallback='')}"
    builddir = f"{prefix}/{config.get('project', 'build_dir', fallback='.build')}"
    outdir = f"{prefix}/{config.get('project', 'out_dir', fallback='out')}"

    os.makedirs(builddir, exist_ok=True)
    curdir = f"{os.getcwd()}/{prefix}"

    log(" - writing project file")
    with open(f'{builddir}/syn.prj', 'w') as f:
        for s in config.get(f'build:{target}', 'src_vhdl', fallback="").split():
            f.write(f"vhdl work {curdir}/{s}\n")
        for s in config.get(f'build:{target}', 'src_verilog', fallback="").split():
            f.write(f"verilog work {curdir}/{s}\n")
        for s in config.get(f'build:{target}', 'src_sysverilog', fallback="").split():
            f.write(f"verilog work {curdir}/{s}\n")

    log(" - writing project generation file")
    with open(f'{builddir}/prj.scr', 'w') as f:
        f.write(f'run\n-ifn syn.prj\n-ofn syn.ngc\n-ifmt mixed\n')
        f.write(f'-top {config.get(f"sources:{target}", "toplevel", fallback="toplevel")}\n')
        f.write(f'-p {device}\n-glob_opt max_delay -opt_mode speed')

    log(" - Executing xst")
    p = subprocess.Popen("xst -intstyle xflow -ifn prj.scr", shell=True, cwd=builddir, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode
    if res:
        log(" - ERROR: return code is", res)
        log(" - copy log")
        os.makedirs(f'{outdir}/{target}', exist_ok=True)
        shutil.copy(f'{builddir}/prj.srp', f'{outdir}/{target}/synth.log')
        return res

    log(" - copy output files")
    os.makedirs(f'{outdir}/{target}', exist_ok=True)
    shutil.copy(f'{builddir}/syn.ngc', f'{outdir}/{target}/synth.ngc')
    shutil.copy(f'{builddir}/prj.srp', f'{outdir}/{target}/synth.log')
    return 0