import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting simulation")
    
    log(" - parsing options")
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    vcdlevels = config.get(f'target.{target}', 'vcdlevels', fallback='1')
    runtime = config.get(f'target.{target}', 'runtime', fallback='100 ns')
    fuse_opts = config.get(f'target.{target}', 'fuse_opts', fallback='')
    isim_opts = config.get(f'target.{target}', 'isim_opts', fallback='')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    fuse_opts = fuse_opts.replace("~D~", prefix)
    isim_opts = isim_opts.replace("~D~", prefix)

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - writing project file")
    with open(f'{build_dir}/sim.prj', 'w') as f:
        for s in files_vhdl:
            if s=='':
                continue
            f.write(f"vhdl work {prefix}/{s}\n")
        for s in files_verilog:
            if s=='':
                continue
            f.write(f"verilog work {prefix}/{s}\n")

    log(" - run fuse")
    p = subprocess.Popen(f"fuse -v 2 {fuse_opts} {toplevel} -prj sim.prj -o sim -incremental > ffuse.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/ffuse.log', f'{out_dir}/fuse.log')

    if res!=0:
        log("ERROR: fuse returned with:", res)
        return res

    log(" - writing simulation file")
    with open(f'{build_dir}/sim.tcl', 'w') as f:
        f.write("onerror {resume}\n")
        f.write("vcd dumpfile sim.vcd\n")
        f.write(f"vcd dumpvars -m {toplevel} -l {vcdlevels}\n")
        f.write("vcd dumpon\n")
        f.write(f"run {runtime}\n")
        f.write("vcd dumpflush\nquit\n")

    log(" - run sim")
    p = subprocess.Popen(f"./sim {isim_opts} -tclbatch sim.tcl > sim.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/sim.log', f'{out_dir}/sim.log')

    if res==0:
        log(" - copy output files")
        shutil.copy(f'{build_dir}/sim.vcd', f'{out_dir}/{target}.vcd')
    else:
        log("ERROR: sim returned with:", res)

    return res