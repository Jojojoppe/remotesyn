import shutil
import os
import time
import subprocess
import html2text

def do(config, target, log, subprocesses, prefix='.'):
  shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
  shutil.rmtree(config.get('project', 'out_dir', fallback='out'), True)

  log(" - parsing options")
  family = config.get(f'target.{target}', 'family', fallback='')
  device = config.get(f'target.{target}', 'device', fallback='')
  toplevel = config.get(f'target.{target}', 'toplevel', fallback='toplevel')
  files_vhdl = config.get(f'target.{target}', 'files_vhdl', fallback='').split()
  files_verilog = config.get(f'target.{target}', 'files_verilog', fallback='').split()
  files_con= config.get(f'target.{target}', 'files_con', fallback='').split()
  build_dir = config.get(f'project', 'build_dir', fallback='build')
  out_dir = config.get(f'project', 'out_dir', fallback='out')

  prefix = f'{os.getcwd()}/{prefix}'
  build_dir = f'{prefix}/{build_dir}'
  out_dir = f'{prefix}/{out_dir}/{target}'

  log(" - creating output directories")
  os.makedirs(build_dir, exist_ok=True)
  os.makedirs(out_dir, exist_ok=True)

  log(" - writing scripts")
  with open(f'{build_dir}/synth.tcl', 'w') as f:
    f.write(f'set_device {device} -name {family}\n')

    for s in files_vhdl:
      if s=='':
        continue
      f.write(f'add_file {prefix}/{s}\n')
    for s in files_verilog:
      if s=='':
        continue
      f.write(f'add_file {prefix}/{s}\n')
    for s in files_con:
      if s=='':
        continue
      f.write(f'add_file {prefix}/{s}\n')
    
    f.write('set_option -synthesis_tool gowinsynthesis\n')
    f.write(f'set_option -output_base_name {toplevel}\n')
    f.write(f'set_option -top_module {toplevel}\n')
    f.write('run syn\n')

  with open(f'{build_dir}/pnr.tcl', 'w') as f:
    f.write(f'set_device {device} -name {family}\n')
    f.write('set_option -synthesis_tool gowinsynthesis\n')
    f.write(f'set_option -output_base_name {toplevel}\n')
    f.write(f'set_option -top_module {toplevel}\n')
    for s in files_con:
      if s=='':
        continue
      f.write(f'add_file {prefix}/{s}\n')
    f.write(f'add_file {build_dir}/impl/gwsynthesis/{toplevel}.vg\n')
    
    f.write('run pnr\n')
  
  log(' - run syntesis')
  p = subprocess.Popen(f"gw_sh synth.tcl",
                       shell = True,
                       cwd = build_dir,
                       stdin = subprocess.DEVNULL,
                       # stdout = subprocess.DEVNULL,
                       # stderr = subprocess.DEVNULL,
                       )

  subprocesses.append(p)
  while p.poll() is None:
    time.sleep(1)
  res = p.returncode

  shutil.copy(f'{build_dir}/impl/gwsynthesis/{toplevel}.log', f'{out_dir}/synth.log')
  if res!=0:
    log("ERROR: synthesis failed with:", res)
    return res
  shutil.copy(f'{build_dir}/impl/gwsynthesis/{toplevel}.vg', f'{out_dir}/synth_netlist.vg')
  with open(f'{build_dir}/impl/gwsynthesis/{toplevel}_syn.rpt.html', 'r') as fin, open(f'{out_dir}/synth_rpt.md', 'w') as fout:
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = True
    text_maker.body_width = 500
    fout.write(text_maker.handle(fin.read()))

  log(' - run PnR')
  p = subprocess.Popen(f"gw_sh pnr.tcl",
                       shell = True,
                       cwd = build_dir,
                       stdin = subprocess.DEVNULL,
                       # stdout = subprocess.DEVNULL,
                       # stderr = subprocess.DEVNULL,
                       )

  subprocesses.append(p)
  while p.poll() is None:
    time.sleep(1)
  res = p.returncode

  shutil.copy(f'{build_dir}/impl/pnr/{toplevel}.log', f'{out_dir}/pnr.log')
  if res!=0:
    log("ERROR: pnr failed with:", res)
    return res
  shutil.copy(f'{build_dir}/impl/pnr/{toplevel}.fs', f'{out_dir}/{toplevel}.fs')
  shutil.copy(f'{build_dir}/impl/pnr/{toplevel}.bin', f'{out_dir}/{toplevel}.bin')
  with open(f'{build_dir}/impl/pnr/{toplevel}.rpt.html', 'r') as fin, open(f'{out_dir}/rpt.md', 'w') as fout:
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = True
    text_maker.body_width = 500
    fout.write(text_maker.handle(fin.read()))
  with open(f'{build_dir}/impl/pnr/{toplevel}.power.html', 'r') as fin, open(f'{out_dir}/power.md', 'w') as fout:
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = True
    text_maker.body_width = 500
    fout.write(text_maker.handle(fin.read()))
  with open(f'{build_dir}/impl/pnr/{toplevel}.pin.html', 'r') as fin, open(f'{out_dir}/pin.md', 'w') as fout:
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = True
    text_maker.body_width = 500
    fout.write(text_maker.handle(fin.read()))
  with open(f'{build_dir}/impl/pnr/{toplevel}_tr_content.html', 'r') as fin, open(f'{out_dir}/timing.md', 'w') as fout:
    text_maker = html2text.HTML2Text()
    text_maker.bypass_tables = False
    text_maker.ignore_links = True
    text_maker.body_width = 500
    fout.write(text_maker.handle(fin.read()))

  return res
