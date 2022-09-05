import shutil
import os
import time
import subprocess

def out(config, target, log, subprocesses, prefix='.'):
    log(" - parsing options")
    device = config.get(f'target.{target}', 'device', fallback='')
    package = config.get(f'target.{target}', 'package', fallback='')
    speedgrade = config.get(f'target.{target}', 'speedgrade', fallback='')
    toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
    netlist_top = config.get(f'target.{target}', 'netlist_top', fallback='toplevel').split()
    files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
    files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
    files_sysverilog = config.get(f'target.{target}', 'files_sysverilog', fallback='').split()
    files_con = config.get(f'target.{target}', 'files_con', fallback='').split()
    files_xci = config.get(f'target.{target}', 'files_xci', fallback='').split()
    opt_opts = config.get(f'target.{target}', 'opt_opts', fallback='')
    place_opts = config.get(f'target.{target}', 'place_opts', fallback='')
    route_opts = config.get(f'target.{target}', 'route_opts', fallback='')
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
        f.write(f"open_checkpoint {out_dir}/post_impl.dcp\n")
        f.write(f"set_property SEVERITY {{Warning}} [get_drc_checks NSTD-1]\nset_property SEVERITY {{Warning}} [get_drc_checks UCIO-1]\n")
        f.write(f"set_property BITSTREAM.General.UnconstrainedPins {{Allow}} [current_design]\n")
        f.write(f"write_debug_probes -force out.ltx\nwrite_bitstream -force -bin_file out.bit\nreport_timing_summary -file timing.log\nreport_power -file power.log\n")
        f.write(f"report_utilization -file util.log\n")
        f.write(f"write_checkpoint -force {out_dir}/{target}.dcp\n")
        f.write(f"open_checkpoint {out_dir}/{target}.dcp\n")
        f.write(f"write_hw_platform -fixed -force -file {out_dir}/{target}.xsa\n")
        f.write(f"write_verilog -force -mode timesim -cell {netlist_top[0]} -rename_top {netlist_top[1]} -sdf_anno true -sdf_file impl_netlist.sdf impl_netlist.v\n") # -nolib
        f.write(f"write_sdf -force -cell {netlist_top[0]} -rename_top {netlist_top[1]} -mode timesim impl_netlist.sdf\n")

    log(" - run vivado")
    p = subprocess.Popen(f"vivado -mode batch -source do.tcl", 
        shell=True, cwd=build_dir, 
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(1)
    res = p.returncode

    log(" - copy logs")
    shutil.copy(f'{build_dir}/vivado.log', f'{out_dir}/out.log')

    if res!=0:
        return res
    
    log(" - copy output files")
    shutil.copy(f'{build_dir}/impl_netlist.v', f'{out_dir}/impl_netlist.v')
    shutil.copy(f'{build_dir}/impl_netlist.sdf', f'{out_dir}/impl_netlist.sdf')
    shutil.copy(f'{build_dir}/timing.log', f'{out_dir}/timing.log')
    shutil.copy(f'{build_dir}/util.log', f'{out_dir}/util.log')
    shutil.copy(f'{build_dir}/power.log', f'{out_dir}/power.log')
    shutil.copy(f'{build_dir}/out.bin', f'{out_dir}/out.bin')
    shutil.copy(f'{build_dir}/out.bit', f'{out_dir}/out.bit')

    return res
