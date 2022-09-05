import shutil
import os
import time
import subprocess

def impl(config, target, log, subprocesses, prefix='.'):
    log(" - parsing options")
    opt_opts = config.get(f'target.{target}', 'opt_opts', fallback='')
    place_opts = config.get(f'target.{target}', 'place_opts', fallback='')
    route_opts = config.get(f'target.{target}', 'route_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - writing project tcl file")
    with open(f'{build_dir}/do.tcl', 'w') as f:
        f.write('set_param general.maxThreads 8\n')
        f.write(f"open_checkpoint {out_dir}/post_synth.dcp\n")
        f.write(f"opt_design {opt_opts}\nplace_design {place_opts}\nroute_design {route_opts}\n")
        f.write(f"write_checkpoint -force post_impl.dcp\n")

    log(" - run vivado")
    p = subprocess.Popen(f"vivado -mode batch -source do.tcl", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/vivado.log', f'{out_dir}/impl.log')

    if res!=0:
        return res
    
    log(" - copy output files")
    shutil.copy(f'{build_dir}/post_impl.dcp', f'{out_dir}/post_impl.dcp')

    return res
