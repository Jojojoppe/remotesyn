import shutil
import os
import time
import subprocess

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting simulation")

    log(" - parsing options")
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    runtime = config.get(f'target.{target}', 'runtime', fallback='100 ns')
    xelab_opts = config.get(f'target.{target}', 'xelab_opts', fallback='')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    files_sysverilog = config.get(f'target.{target}', 'files_sysverilog', fallback='').split()
    files_xci = config.get(f'target.{target}', 'files_xci', fallback='').split()
    files_other = config.get(f'target.{target}', 'files_other', fallback='').split()
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    xelab_opts = xelab_opts.replace('\n', ' ')

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - writing project tcl file")
    with open(f'{build_dir}/do.tcl', 'w') as f:
        f.write('set_param general.maxThreads 8\n')
        f.write(f'create_project -force sim sim\n')
        for s in files_vhdl:
            f.write(f"add_files -norecurse -scan_for_includes \"{prefix}/{s}\"\n")
            f.write(f"import_files -norecurse \"{prefix}/{s}\"\n")
        for s in files_verilog:
            f.write(f"add_files -norecurse -scan_for_includes \"{prefix}/{s}\"\n")
            f.write(f"import_files -norecurse \"{prefix}/{s}\"\n")
        for s in files_sysverilog:
            f.write(f"add_files -norecurse -scan_for_includes \"{prefix}/{s}\"\n")
            f.write(f"import_files -norecurse \"{prefix}/{s}\"\n")
        for s in files_xci:
            f.write(f"add_files -norecurse -scan_for_includes \"{prefix}/{s}\"\n")
        for s in files_other:
            f.write(f"add_files -norecurse -scan_for_includes \"{prefix}/{s}\"\n")
            f.write(f"import_files -norecurse \"{prefix}/{s}\"\n")
        # TODO C files for VPI

        f.write(f"set_property top {toplevel} [get_filesets sim_1]\n")
        f.write("set_property top_lib xil_defaultlib [get_filesets sim_1]\n")
        f.write("launch_simulation -noclean_dir -scripts_only -absolute_path\n")

    log(" - run vivado")

    p = subprocess.Popen(f"vivado -mode batch -source do.tcl", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/vivado.log', f'{out_dir}/synth.log')

    if res!=0:
        log("ERROR: vivado returned with", res)
        return res

    log(" - patch run scripts")

    p = subprocess.Popen(f'sed -i "s/xelab/xelab {xelab_opts}/g" elaborate.sh', 
        shell=True, cwd=f'{build_dir}/sim/sim.sim/sim_1/behav/xsim', 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    if res!=0:
        log("ERROR: patch returned with", res)
        return res

    log(" - copy other files to simulation environment")
    for f in files_other:
        shutil.copy(f'{prefix}/{f}', f'{build_dir}/sim/sim.sim/sim_1/behav/xsim')
        if f.endswith('.sdf'):
            #patch sdf file
            fname = f.split('/')[-1]
            log(f"  (patching {fname})")
            p = subprocess.Popen(f"sed -i '/ \/I /d' {fname} && sed -i '/glbl.v/d' *.prj", 
                shell=True, cwd=f'{build_dir}/sim/sim.sim/sim_1/behav/xsim', 
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocesses.append(p)
            while p.poll() is None:
                time.sleep(1)
            res = p.returncode

            if res!=0:
                log("ERROR: Patching went wrong...")
                return res

    log(" - compile")

    p = subprocess.Popen(f'bash compile.sh', 
        shell=True, cwd=f'{build_dir}/sim/sim.sim/sim_1/behav/xsim', 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/sim/sim.sim/sim_1/behav/xsim/compile.log', f'{out_dir}/compile.log')

    if res!=0:
        log("ERROR: compile returned with", res)
        return res

    log(" - elaborate")

    p = subprocess.Popen(f'bash elaborate.sh', 
        shell=True, cwd=f'{build_dir}/sim/sim.sim/sim_1/behav/xsim', 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/sim/sim.sim/sim_1/behav/xsim/elaborate.log', f'{out_dir}/elaborate.log')

    if res!=0:
        log("ERROR: elaborate returned with", res)
        return res

    log(" - write simulation script")
    with open(f'{build_dir}/sim/sim.sim/sim_1/behav/xsim/{toplevel}.tcl', 'w') as f:
        f.write(f"open_vcd out.vcd\nlog_vcd\nrun {runtime}\nclose_vcd\nquit\n")

    log(" - simulate")

    p = subprocess.Popen(f'bash simulate.sh', 
        shell=True, cwd=f'{build_dir}/sim/sim.sim/sim_1/behav/xsim', 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/sim/sim.sim/sim_1/behav/xsim/simulate.log', f'{out_dir}/simulate.log')

    if res!=0:
        log("ERROR: patch simulate with", res)
        return res

    log(" - copy output files")
    shutil.copy(f'{build_dir}/sim/sim.sim/sim_1/behav/xsim/out.vcd', f'{out_dir}/out.vcd')

    return res

