from distutils.command.build import build
import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting cocotb")

    log(" - parsing options")
    toplevels = config.get(f'target.{target}', 'toplevels', fallback='').split()
    simulator = config.get(f'target.{target}', 'simulator', fallback='ghdl')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    files_python = config.get(f'target.{target}', 'files_python', fallback='').split()
    files_python_other = config.get(f'target.{target}', 'files_python_other', fallback='').split()
    files_other = config.get(f'target.{target}', 'files_other', fallback='').split()
    toplevel_langs = config.get(f'target.{target}', 'toplevel_langs', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}%%'.replace('/.%%', '').replace('%%', '')
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - copy needed files")
    for f in files_python_other:
        shutil.copy(f"{prefix}/{f}", f"{build_dir}/{os.path.basename(f)}")
    for f in files_other:
        d = os.path.dirname(f)
        os.makedirs(f"{build_dir}/{d}", exist_ok=True)
        shutil.copy(f"{prefix}/{f}", f"{build_dir}/{f}")

    res = 0

    i = 0
    for pfile in files_python:
        
        log(" - copy", pfile)
        shutil.copy(f"{prefix}/{pfile}", build_dir)

        log(" - writing Makefile for", pfile)
        with open(f'{build_dir}/Makefile', 'w') as f:
            f.write(f".SILENT:\nSIM ?= {simulator}\nTOPLEVEL_LANG ?= {toplevel_langs[i]}\nWAVES = 1\n")
            f.write(f"TOPLEVEL = {toplevels[i]}\nMODULE = {'.'.join(os.path.basename(pfile).split('.')[0:-1])}\n")
            for vfile in files_vhdl:
                f.write(f"VHDL_SOURCES += {prefix}/{vfile}\n")
            for vfile in files_verilog:
                f.write(f"VERILOG_SOURCES += {prefix}/{vfile}\n")

            if simulator=='ghdl':
                f.write(f"SIM_ARGS += --vcd={os.path.basename(pfile)}.vcd\n")
                
            f.write("include $(shell cocotb-config --makefiles)/Makefile.sim\n")

        log(" - start cocotb")
        p = subprocess.Popen(f"make 2>&1 | tee {os.path.basename(pfile)}.log", 
            shell=True, cwd=build_dir, 
            stdin=subprocess.DEVNULL, 
            # stdout=subprocess.DEVNULL, 
            # stderr=subprocess.DEVNULL
            )
        subprocesses.append(p)
        while p.poll() is None:
            time.sleep(1)
        res |= p.returncode

        shutil.copy(f"{build_dir}/{os.path.basename(pfile)}.log", out_dir)

        if simulator=='ghdl':
            shutil.copy(f"{build_dir}/{os.path.basename(pfile)}.vcd", out_dir)
        elif simulator=='questa':
            os.system(f'wlf2vcd -o {out_dir}/{os.path.basename(pfile)}.vcd {build_dir}/vsim.wlf')

        i += 1

    return res