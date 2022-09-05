import shutil
import os
import time
import subprocess

from .util_VIVADO.synth import synth
from .util_VIVADO.impl import impl
from .util_VIVADO.out import out

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
    
    log("Synthesize:")

    res = synth(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: vivado returned with", res)
        return res

    log("Implement")

    res = impl(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: vivado returned with", res)
        return res

    log("Generate output files")

    res = out(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: vivado returned with", res)
        return res