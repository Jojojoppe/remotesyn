from .util_ISE.xst import xst
from .util_ISE.ngdbuild import ngdbuild
from .util_ISE.map import map
from .util_ISE.par import par
from .util_ISE.netgen import netgen

def do(config, target, log, subprocesses, prefix='.'):
    log("Syntesize:")

    res = xst(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: xst returned with", res)
        return res

    log("Implement")

    res = ngdbuild(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: ngdbuild returned with", res)
        return res

    res = map(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: map returned with", res)
        return res

    res = par(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: par returned with", res)
        return res

    res = netgen(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: netgen returned with", res)
        return res