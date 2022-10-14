import shutil
import os
import time
import subprocess

def trce(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    trce_opts = config.get(f'target.{target}', 'trce_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run trce")
    p = subprocess.Popen(f"trce -intstyle xflow {trce_opts} -v 3 -s 2 -n 3 -fastpaths {out_dir}/{target}.ncd {out_dir}/{target}.pcf", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/{target}.twr', f'{out_dir}/timing.log')
    shutil.copy(f'{build_dir}/{target}.twx', f'{out_dir}/timing.twx')

    return res