# iverilog.py
import shutil
import os
import time
import subprocess

def _execp(cmd, subprocesses, cwd):
    p = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        # stdout/stderr visible so tee can capture; keep quiet if you prefer:
        # stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    subprocesses.append(p)
    while p.poll() is None:
        time.sleep(0.2)
    return p.returncode

def do(config, target, log, subprocesses, prefix='.'):
    # fresh build dir
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Starting simulation (iverilog)")

    # --- parse options (keep names consistent with your other toolchains) ---
    toplevel        = config.get(f'target.{target}', 'toplevel',       fallback='toplevel')
    ivl_opts        = config.get(f'target.{target}', 'ivl_opts',       fallback='')
    vvp_opts        = config.get(f'target.{target}', 'vvp_opts',       fallback='')
    runtime         = config.get(f'target.{target}', 'runtime',        fallback='')  # optional; TB can honor +stop_time
    files_verilog   = config.get(f'target.{target}', 'files_verilog',  fallback='').split()
    files_sysverilog= config.get(f'target.{target}', 'files_sysverilog', fallback='').split()
    files_vhdl      = config.get(f'target.{target}', 'files_vhdl',     fallback='').split()
    files_other     = config.get(f'target.{target}', 'files_other',    fallback='').split()
    build_dir       = config.get('project', 'build_dir',               fallback='build')
    out_dir_root    = config.get('project', 'out_dir',                 fallback='out')

    # normalize paths
    prefix   = f'{os.getcwd()}/{prefix}'
    build_dir= f'{prefix}/{build_dir}'
    out_dir  = f'{prefix}/{out_dir_root}/{target}'

    # minor sanitization
    ivl_opts = ivl_opts.replace('\n', ' ')
    vvp_opts = vvp_opts.replace('\n', ' ')

    # --- create dirs ---
    log(" - creating output directories")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # --- copy extra needed files into build dir (keeping tree) ---
    if files_other:
        log(" - copy needed files")
    for f in files_other:
        if not f: continue
        d = os.path.dirname(f)
        if d:
            os.makedirs(f"{build_dir}/{d}", exist_ok=True)
        shutil.copy(f"{prefix}/{f}", f"{build_dir}/{f}")

    # --- guard: VHDL not supported by Icarus ---
    if any(s for s in files_vhdl if s.strip()):
        log("WARNING: VHDL files listed but iverilog does not support VHDL — ignoring them")

    # --- build source list (order as provided) ---
    sources = []
    for s in files_verilog:
        if s: sources.append(f'"{prefix}/{s}"')
    for s in files_sysverilog:
        if s: sources.append(f'"{prefix}/{s}"')

    if not sources:
        log("ERROR: no Verilog/SystemVerilog sources provided")
        return 1

    # --- decide standard (enable SV if any sysverilog files or if user asked) ---
    needs_sv = len([1 for _ in files_sysverilog if _]) > 0
    std_flag = "-g2012" if needs_sv and "-g" not in ivl_opts and "-g2012" not in ivl_opts else ""

    # --- compile ---
    log(" - compile (iverilog)")
    # -s <top> sets the toplevel; produce sim.vvp; tee compile log
    # You can add include dirs/defines via ivl_opts (e.g., -Iinc -DNAME=VALUE)
    cmd_compile = f'iverilog -o sim.vvp -s {toplevel} {std_flag} {ivl_opts} ' + " ".join(sources) + ' 2>&1 | tee comp.log'
    res = _execp(cmd_compile, subprocesses, build_dir)

    # logs
    shutil.copy(f'{build_dir}/comp.log', f'{out_dir}/compile.log')
    if res != 0:
        log("ERROR: iverilog returned with", res)
        return res

    # --- simulate ---
    log(" - simulate (vvp)")
    # If your TB supports +stop_time=<time>, we pass it from 'runtime' (e.g., "1000us" -> +stop_time=1000us)
    plusargs = []
    if runtime and runtime.strip().lower() != 'all':
        rt = runtime.replace(" ", "")
        plusargs.append(f'+stop_time={rt}')   # your TB can $value$plusargs("stop_time=%s", str)

    cmd_run = f'vvp {vvp_opts} sim.vvp ' + " ".join(plusargs) + ' 2>&1 | tee sim.log'
    res = _execp(cmd_run, subprocesses, build_dir)

    # copy sim log
    shutil.copy(f'{build_dir}/sim.log', f'{out_dir}/simulate.log')

    # --- copy outputs if present ---
    # Expect the TB to do $dumpfile("out.vcd"); $dumpvars; (or use your own filename)
    vcd_candidates = ["out.vcd", f"{toplevel}.vcd", "sim.vcd"]
    copied = False
    for vcd in vcd_candidates:
        src = f'{build_dir}/{vcd}'
        if os.path.exists(src):
            shutil.copy(src, f'{out_dir}/out.vcd')
            copied = True
            break
    if not copied:
        log("NOTE: no VCD found (ensure your TB calls $dumpfile(\"out.vcd\") and $dumpvars)")

    return res
