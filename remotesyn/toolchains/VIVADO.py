import shutil
import os
import time
import subprocess

from .util_VIVADO.synth import synth

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
    
    log("Synthesize:")

    res = synth(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: vivado returned with", res)
        return res