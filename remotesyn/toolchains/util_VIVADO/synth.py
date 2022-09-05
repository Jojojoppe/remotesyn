import shutil
import os
import time
import subprocess

def synth(config, target, log, subprocesses, prefix='.'):
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    netlist_top = config.get(f'target.{target}', 'netlist_top', fallback='toplevel')
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    files_sysverilog = config.get(f'target.{target}', 'files_sysverilog', fallback='').split()
    files_con = config.get(f'target.{target}', 'files_con', fallback='').split()
    files_xci = config.get(f'target.{target}', 'files_xci', fallback='').split()
    synth_opts = config.get(f'target.{target}', 'synth_opts', fallback='')
    build_dir = config.get(f'project', 'build_dir', fallback='build')
    out_dir = config.get(f'project', 'out_dir', fallback='out')

    prefix = f'{os.getcwd()}/{prefix}'
    build_dir = f'{prefix}/{build_dir}'
    out_dir = f'{prefix}/{out_dir}/{target}'

    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    log(" - writing project tcl file")
    with open(f'{build_dir}/do.tcl', 'w') as f:
        f.write('set_param general.maxThreads 8\n')
        for s in files_vhdl:
            f.write(f"read_vhdl \"{prefix}/{s}\"\n")
        for s in files_verilog:
            f.write(f"read_verilog \"{prefix}/{s}\"\n")
        for s in files_sysverilog:
            f.write(f"read_verilog -sv \"{prefix}/{s}\"\n")
        for s in files_con:
            f.write(f"read_xdc \"{prefix}/{s}\"\n")
        for s in files_xci:
            f.write(f"read_ip \"{prefix}/{s}\"\n")

        f.write(f"set_property part {device}{package}{speedgrade} [current_project]\n")
        f.write(f"upgrade_ip [get_ips]\ngenerate_target all [get_ips]\nsynth_ip [get_ips]\n")
        f.write(f"synth_design -top {toplevel} -part {device}{package}{speedgrade} {synth_opts}\n")
        f.write(f"write_checkpoint -force post_synth.dcp\nwrite_verilog -force -mode timesim -cell {netlist_top} -sdf_anno true -nolib netlist.v\n")
        f.write(f"write_sdf -force -cell {netlist_top} -mode timesim netlist.sdf\n")

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
        return res
    
    log(" - copy output files")
    shutil.copy(f'{build_dir}/netlist.v', f'{out_dir}/synth_netlist.v')
    shutil.copy(f'{build_dir}/netlist.sdf', f'{out_dir}/synth_netlist.sdf')
    shutil.copy(f'{build_dir}/post_synth.dcp', f'{out_dir}/post_synth.dcp')

    return res
