import shutil
import os
import time
import subprocess

def bitgen(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    bitgen_opts = config.get(f'target.{target}', 'bitgen_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run bitgen")
    p = subprocess.Popen(f"bitgen -intstyle xflow {bitgen_opts} -g Binary:Yes -w {out_dir}/{target}.ncd {target}.bit {out_dir}/{target}.pcf 2> bitgen.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/bitgen.log', f'{out_dir}/bitgen.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/{target}.bit', f'{out_dir}/{target}.bit')
        shutil.copy(f'{build_dir}/{target}.bin', f'{out_dir}/{target}.bin')

    return res