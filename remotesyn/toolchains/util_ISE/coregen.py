import shutil
import os
import time
import subprocess

def coregen(config, target, log, subprocesses, prefix='.') -> int:
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    family = config.get(f'target.{target}', 'family', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    coregen_opts = config.get(f'target.{target}', 'coregen_opts', fallback='')
    files_def = config.get(f'target.{target}', 'files_def', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    res = 0

    for fxco in files_def:
        cname = fxco.split('/')[-1].split('.')[0]
        
        log(" - Generating", cname, "...")

        log(" - Writing device file")
        with open(f"{build_dir}/coregen_{cname}.cgp", "w") as f:
            f.write(f'SET busformat = BusFormatAngleBracketNotRipped\n')
            f.write(f'SET designentry = VHDL\n')
            f.write(f'SET device = {device}\n')
            f.write(f'SET devicefamily = {family}\n')
            f.write(f'SET package = {package}\n')
            f.write(f'SET speedgrade = {speedgrade}\n')
            f.write(f'SET flowvendor = Other\n')
            f.write(f'SET verilogsim = true\n')
            f.write(f'SET vhdlsim = true\n')
            f.write(f'SET implementationfiletype = ngc\n')

        log(" - run coregen")
        p = subprocess.Popen(f"coregen {coregen_opts} -p coregen_{cname}.cgp -b {prefix}/{fxco}", 
            shell=True, cwd=build_dir, 
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocesses.append(p)
        while p.poll() is None:
            time.sleep(1)
        res = p.returncode

        log(" - copy logs")
        shutil.copy(f'{build_dir}/coregen.log', f'{out_dir}/coregen_{cname}.log')

        if res==0:
            log(" - copy output files")
            try:
                shutil.copy(f'{build_dir}/{cname}.vhd', f'{out_dir}/{cname}.vhd')
            except FileNotFoundError:
                pass
            try:
                shutil.copy(f'{build_dir}/{cname}.v', f'{out_dir}/{cname}.v')
            except FileNotFoundError:
                pass
            try:
                shutil.copy(f'{build_dir}/{cname}.ngc', f'{out_dir}/{cname}.ngc')
            except FileNotFoundError:
                pass
            try:
                shutil.copy(f'{build_dir}/{cname}.xco', f'{out_dir}/{cname}.xco')
            except FileNotFoundError:
                pass
        else:
            return res

    return res