import shutil
import os
import time
import subprocess

def par(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    par_opts = config.get(f'target.{target}', 'par_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    devstring = f'{device}{speedgrade}-{package}'
    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run par")
    p = subprocess.Popen(f"par -intstyle xflow -ol high -xe n {par_opts} -w impl.map.ncd impl.pcf | tee par.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/par.log', f'{out_dir}/par.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/impl.pcf', f'{out_dir}/{target}.pcf')
        shutil.copy(f'{build_dir}/impl.pcf.ncd', f'{out_dir}/{target}.ncd')

    return res