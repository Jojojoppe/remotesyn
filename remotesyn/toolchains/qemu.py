import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting QEMU simulation")

    log(" - parsing options")
    files_executable = config.get(f'target.{target}', 'files_executable', fallback='')
    arch = config.get(f'target.{target}', 'arch', fallback='arm')
    machine = config.get(f'target.{target}', 'machine', fallback='xilinx-zynq-a9')
    ram = config.get(f'target.{target}', 'ram', fallback='500M')
    extra_opts = config.get(f'target.{target}', 'extra_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - run QEMU, quit r(m)build to stop")
    p = subprocess.Popen(f"qemu-system-{arch} -machine {machine} -kernel {prefix}/{files_executable} {extra_opts} -m {ram} -nographic | tee run.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode
    
    log(" - copy logs")
    shutil.copy(f'{build_dir}/run.log', f'{out_dir}/run.log')

    return 0