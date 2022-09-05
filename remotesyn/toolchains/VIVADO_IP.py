from distutils.command.build import build
import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
    
    log("Generate IP's:")

    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    family = config.get(f'target.{target}', 'family', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    files_tcl = config.get(f'target.{target}', 'files_tcl', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    for tcl in files_tcl:
        cname = tcl.split('/')[-1].split('.')[0]
        
        log(" - Generating", cname, "...")

        log(" - writing project tcl file")
        with open(f'{build_dir}/do.tcl', 'w') as f:
            f.write(f"file mkdir {cname}\ncreate_project -in_memory\nset_property part {device}{package}{speedgrade} [current_project]\n")
            f.write(f"source {prefix}/{tcl}\n")
            f.write(f"export_ip_user_files -of_objects [get_files {cname}/{cname}/{cname}.xci ] -no_script -sync -force -quiet\n")
            f.write(f"upgrade_ip [get_ips {cname}]\ngenerate_target all [get_ips {cname}]\n")

        log(" - run vivado")
        p = subprocess.Popen(f"vivado -mode batch -source do.tcl", 
            shell=True, cwd=build_dir, 
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocesses.append(p)
        while p.poll() is None:
            time.sleep(1)
        res = p.returncode

        log(" - copy logs")
        shutil.copy(f'{build_dir}/vivado.log', f'{out_dir}/vivado_{cname}.log')

        if res==0:
            log(" - copy output files")
            shutil.rmtree(f'{out_dir}/{cname}', True)
            shutil.copytree(f'{build_dir}/.gen/sources_1/ip/{cname}', f'{out_dir}/{cname}', dirs_exist_ok=True)
            shutil.copy(f'{build_dir}/.srcs/sources_1/ip/{cname}/{cname}.xci', f'{out_dir}/{cname}/{cname}.xci')
        else:
            log("ERROR: vivado returned with:", res)
            return res

