import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting make build process")
    
    log(" - parsing options")
    files_makefile = config.get(f'target.{target}', 'files_makefile', fallback='')
    buildroot = config.get(f'target.{target}', 'buildroot', fallback='.')
    output_files = config.get(f'target.{target}', 'output_files', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - Copy makefile to build directory")
    shutil.copy(f"{prefix}/{files_makefile}", f"{build_dir}/Makefile")

    log(" - run make")
    p = subprocess.Popen(f"BUILDROOT={prefix}/{buildroot} make 2>make.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/make.log', f'{out_dir}/make.log')

    if res!=0:
        log("ERROR: make returned with:", res)
        return res

    log(" - copy output files")
    for f in output_files:
        shutil.copy(f'{build_dir}/{f}', f'{out_dir}/{os.path.basename(f)}')

    return 0