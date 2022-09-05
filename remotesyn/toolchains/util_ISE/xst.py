import shutil
import os
import time
import subprocess

def xst(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    xst_opts = config.get(f'target.{target}', 'xst_opts', fallback='')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    devstring = f'{device}{speedgrade}-{package}'
    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - writing project file")
    with open(f'{build_dir}/syn.prj', 'w') as f:
        for s in files_vhdl:
            if s=='':
                continue
            f.write(f"vhdl work {prefix}/{s}\n")
        for s in files_verilog:
            if s=='':
                continue
            f.write(f"verilog work {prefix}/{s}\n")

    log(" - writing project generation file")
    with open(f'{build_dir}/prj.scr', 'w') as f:
        f.write(f'run\n-ifn syn.prj\n-ofn syn.ngc\n-ifmt mixed\n')
        f.write(f'-top {toplevel}\n')
        f.write(f'-p {devstring}\n-glob_opt max_delay -opt_mode speed')

    log(" - run xst")
    p = subprocess.Popen(f"xst -intstyle xflow {xst_opts} -ifn prj.scr", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/prj.srp', f'{out_dir}/xst.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/syn.ngc', f'{out_dir}/{target}.ngc')

    return res