from .util_ISE.xst import xst
from .util_ISE.ngdbuild import ngdbuild
from .util_ISE.map import map
from .util_ISE.par import par
from .util_ISE.netgen import netgen
from .util_ISE.bitgen import bitgen
from .util_ISE.trce import trce
from .util_ISE.coregen import coregen

import shutil

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
    
    log("Generate IP's:")

    res = coregen(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: coregen returned with", res)
        return res