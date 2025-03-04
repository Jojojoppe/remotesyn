from importlib.metadata import files
import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    # shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting simulation")

    log(" - parsing options")
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    runtime = config.get(f'target.{target}', 'runtime', fallback='100 ns')
    vsim_opts = config.get(f'target.{target}', 'vsim_opts', fallback='')
    vcom_opts = config.get(f'target.{target}', 'vcom_opts', fallback='')
    vlog_opts = config.get(f'target.{target}', 'vlog_opts', fallback='')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    files_sysverilog = config.get(f'target.{target}', 'files_sysverilog', fallback='').split()
    files_c = config.get(f'target.{target}', 'files_c', fallback='').split()
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

    files_c_wp = {f'{prefix}/{f}' for f in files_c}

    log(" - writing compile file")
    with open(f'{build_dir}/do.sh', 'w') as f:
        f.write(f'vlib work\nvmap work work\n')
        for s in files_verilog:
            f.write(f"vlog {vlog_opts} {prefix}/{s}\n")
        for s in files_vhdl:
            f.write(f"vcom {vcom_opts} {prefix}/{s}\n")
        for s in files_sysverilog:
            f.write(f"vlog -sv {vlog_opts} {prefix}/{s}\n")
        f.write(f"gcc -g -fPIC -shared -Bsymbolic -o import.so {' '.join(files_c_wp)}\n")
        extra = vsim_opts
        if len(files_c_wp)>0:
            extra = ' -sv_lib import'
        f.write(f"vsim -c -do do.do {extra} -vcd=+multid+vhvar -vcddump=out.vcd {toplevel}")

    log(" - writing do file")
    rtime = "-all"
    if runtime != "all":
        rtime = runtime
    with open(f'{build_dir}/do.do', 'w') as f:
        # f.write(f"vcd file out.vcd\n vcd add -r -in -out -inout -internal -ports *\nrun {rtime}\nquit\n");
        f.write(f"\nrun {rtime}\nquit\n");

    log(" - run vsim")
    p = subprocess.Popen(f"bash ./do.sh 2>&1 | tee do.log", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, 
        #stdout=subprocess.DEVNULL, 
        #stderr=subprocess.DEVNULL
        )
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/do.log', f'{out_dir}/do.log')

    if res!=0:
        log("ERROR: vsim returned with", res)
        return res

    log(" - copy output files")
    shutil.copy(f'{build_dir}/out.vcd', f'{out_dir}/out.vcd')

    return 0
