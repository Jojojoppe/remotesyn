from .util_ISE.xst import xst
from .util_ISE.ngdbuild import ngdbuild
from .util_ISE.map import map
from .util_ISE.par import par
from .util_ISE.netgen import netgen
from .util_ISE.bitgen import bitgen
from .util_ISE.trce import trce

import shutil

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)

    log("Syntesize:")

    res = xst(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: xst returned with", res)
        return res

    log("Implement")

    res = ngdbuild(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: ngdbuild returned with", res)
        return res

    res = map(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: map returned with", res)
        return res

    res = par(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: par returned with", res)
        return res

    log("Generate output files")

    res = netgen(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: netgen returned with", res)
        return res

    res = bitgen(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: bitgen returned with", res)
        return res

    log("Analyze design")

    res = trce(config, target, log, subprocesses, prefix)
    if res != 0:
        log("ERROR: trce returned with", res)
        return res

    return 0