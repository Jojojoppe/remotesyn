import shutil
import os
import time
import subprocess

def netgen(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    netgen_opts = config.get(f'target.{target}', 'netgen_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run netgen")
    p = subprocess.Popen(f"netgen -intstyle xflow -sim -ofmt verilog -w -insert_glbl true -sdf_anno true {netgen_opts} -ism {out_dir}/{target}.ncd > netgen.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/netgen.log', f'{out_dir}/netgen.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/{target}.v', f'{out_dir}/{target}.v')
        shutil.copy(f'{build_dir}/{target}.sdf', f'{out_dir}/{target}.sdf')

    return res