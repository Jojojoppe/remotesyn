import shutil
import os
import time
import subprocess

def map(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    map_opts = config.get(f'target.{target}', 'map_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    devstring = f'{device}{speedgrade}-{package}'
    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run map")
    p = subprocess.Popen(f"map -intstyle xflow -p {devstring} -detail {map_opts} -ol high -xe n -w {out_dir}/{target}.ngd -o impl.map.ncd impl.pcf", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/impl.map.mrp', f'{out_dir}/map.log')

    return res