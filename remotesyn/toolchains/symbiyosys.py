import shutil
import os
import time
import subprocess

def execp(cmd, subprocesses, cwd):
    p = subprocess.Popen(cmd, 
        shell=True, cwd=cwd, 
        stdin=subprocess.DEVNULL, 
        # stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode
    return res

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting formal verification")
    
    log(" - parsing options")
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    runtime = config.get(f'target.{target}', 'runtime', fallback='100 ns')
    sby_opts = config.get(f'target.{target}', 'sby_opts', fallback='')
    files_sby = config.get(f'target.{target}', 'files_sby', fallback='').split()
    files_other = config.get(f'target.{target}', 'files_other', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - copy needed files")
    for f in files_other:
        d = os.path.dirname(f)
        os.makedirs(f"{build_dir}/{d}", exist_ok=True)
        shutil.copy(f"{prefix}/{f}", f"{build_dir}/{f}")

    res = 0
    for f in files_sby:
        log(" - running sby for", f)
        d = os.path.dirname(f)
        os.makedirs(f"{build_dir}/{d}", exist_ok=True)
        shutil.copy(f"{prefix}/{f}", f"{build_dir}/{f}")

        res = execp(f"sby --prefix sby_{os.path.basename(f)} --yosys \"yosys -m ghdl\" {sby_opts} -f {f}", subprocesses, build_dir)

        log(" - copy logs and output files")
        oname = f'sby_{os.path.basename(f)}'
        for d in os.listdir(f'{build_dir}'):
            if os.path.isdir(f'{build_dir}/{d}') and d.startswith(oname):
                shutil.copy(f'{build_dir}/{d}/logfile.txt', f'{out_dir}/{d}.log')
                try:
                    shutil.copytree(f'{build_dir}/{d}/engine_0', f'{out_dir}/{d}', dirs_exist_ok=True)
                except FileNotFoundError:
                    pass

        if res!=0:
            log(" - [-]")
        else:
            log(" - [+]")

    
    return 0