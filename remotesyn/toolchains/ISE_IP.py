from .util_ISE.coregen import coregen

import shutil

def do(config, target, log, subprocesses, prefix='.'):
    shutil.rmtree(config.get('project', 'build_dir', fallback='build'), True)
    
    log("Generate IP's:")

    res = coregen(config, target, log, subprocesses, prefix)
    if res != 0:
        print("ERROR: coregen returned with", res)
        return res

    return 0