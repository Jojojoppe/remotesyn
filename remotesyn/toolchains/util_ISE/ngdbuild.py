import shutil
import os
import time
import subprocess

def ngdbuild(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    ngdbuild_opts = config.get(f'target.{target}', 'ngdbuild_opts', fallback='')
    files_con = config.get(f'target.{target}', 'files_con', fallback='').split(' ')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    devstring = f'{device}{speedgrade}-{package}'
    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run ngdbuild")
    p = subprocess.Popen(f"ngdbuild -intstyle xflow -p {devstring} -uc {prefix}/{files_con[0]} {ngdbuild_opts} {out_dir}/{target}.ngc impl.ngd", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/impl.bld', f'{out_dir}/ngdbuild.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/impl.ngd', f'{out_dir}/{target}.ngd')

    return res