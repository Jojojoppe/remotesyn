from asyncio import constants
import threading
import shutil
import os
import time
import subprocess
import signal
import random

def needed_files(config, target) -> list:
    if not config.has_section(f'build:{target}'):
        print("ERROR: config file has no build section for target")
        return None
    outdir = f"{config.get('project', 'out_dir', fallback='out')}"
    needed_files = [
        f'{outdir}/{target}/synth.ngc',
    ]
    for s in config.get(f'build:{target}', 'constraints', fallback="").split():
        needed_files.append(s)
    return needed_files

def generated_files(config, target) -> list:
    outdir = f"{config.get('project', 'out_dir', fallback='out')}"
    return [
        f'{outdir}/{target}/impl.ngd',
        f'{outdir}/{target}/impl-ngd.log',
    ]

def do(config, target, log, subprocesses, prefix='.') -> int:
    log("Implement:")

    if not config.has_section(f'build:{target}'):
        log("ERROR: config file has no build section for target")
        return 1

    devtarget = f'target:{config.get(f"build:{target}", "target", fallback="")}'
    if not config.has_section(devtarget):
        log("ERROR: config file has no section for device target")
        return 1

    device = f"{config.get(devtarget, 'device', fallback='')}{config.get(devtarget, 'speedgrade', fallback='')}-{config.get(devtarget, 'package', fallback='')}"
    builddir = f"{prefix}/{config.get('project', 'build_dir', fallback='.build')}"
    outdir = f"{prefix}/{config.get('project', 'out_dir', fallback='out')}"

    os.makedirs(builddir, exist_ok=True)
    curdir = f"{os.getcwd()}/{prefix}"

    contstraints = []
    for s in config.get(f'build:{target}', 'constraints', fallback="").split():
        contstraints.append(f"{curdir}/{s}")

    log(" - Executing ngdbuild")
    p = subprocess.Popen(f"ngdbuild -intstyle xflow -p {device} -uc {contstraints[0]} {curdir}/{outdir}/{target}/synth.ngc impl.ngd", shell=True, cwd=builddir, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode
    if res:
        log(" - ERROR: return code is", res)
        log(" - copy log")
        os.makedirs(f'{outdir}/{target}', exist_ok=True)
        shutil.copy(f'{builddir}/impl.bld', f'{outdir}/{target}/impl-ngd.log')
        return res

    log(" - copy output files")
    os.makedirs(f'{outdir}/{target}', exist_ok=True)
    shutil.copy(f'{builddir}/impl.ngd', f'{outdir}/{target}/impl.ngd')
    shutil.copy(f'{builddir}/impl.bld', f'{outdir}/{target}/impl-ngd.log')
    return 0