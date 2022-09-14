import shutil
import os
import time
import subprocess

def execp(cmd, subprocesses, cwd):
    p = subprocess.Popen(cmd, 
        shell=True, cwd=cwd, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode
    return res

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting simulation")
    
    log(" - parsing options")
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    runtime = config.get(f'target.{target}', 'runtime', fallback='100 ns')
    ghdla_opts = config.get(f'target.{target}', 'ghdla_opts', fallback='')
    ghdle_opts = config.get(f'target.{target}', 'ghdle_opts', fallback='')
    ghdlr_opts = config.get(f'target.{target}', 'ghdlr_opts', fallback='')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
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

    log(" - analyze files")
    res = 0
    for f in files_vhdl:
        res = execp(f"echo +++{f} >> a.log && ghdl -a {ghdla_opts} {prefix}/{f} 2>> a.log", subprocesses, build_dir)
        if res!=0:
            break
    log(" - copy logs")
    shutil.copy(f'{build_dir}/a.log', f'{out_dir}/a.log')
    if res!=0:
        log("ERROR: ghdl -a returned with", res)
        return res

    log(" - elaborate")
    res = execp(f"echo {toplevel} >> e.log && ghdl -e {ghdle_opts} {toplevel} 2>> e.log", subprocesses, build_dir)
    log(" - copy logs")
    shutil.copy(f'{build_dir}/e.log', f'{out_dir}/e.log')
    if res!=0:
        log("ERROR: ghdl -e returned with", res)
        return res

    log(" - simulate")
    extra = ''
    if runtime!='all':
        extra = f'--stop-time={runtime.replace(" ", "")}'
    res = execp(f"echo {toplevel} >> r.log && ghdl -r {ghdlr_opts} {extra} {toplevel} --vcd=out.vcd 2>&1 1>> r.log", subprocesses, build_dir)
    log(" - copy logs")
    shutil.copy(f'{build_dir}/r.log', f'{out_dir}/r.log')
    # Ignore simulation errors: vhdl stopping with failure results in returned with 1
    # if res!=0:
    #     log("ERROR: ghdl -r returned with", res)
    #     return res

    log(" - copy output files")
    shutil.copy(f'{build_dir}/out.vcd', f'{out_dir}/out.vcd')

    return 0