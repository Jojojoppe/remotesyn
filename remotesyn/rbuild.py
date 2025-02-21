#!/usr/bin/env python3

import configparser
from re import sub
import sys
import signal

def log(*args):
    print(*args)
    sys.stdout.flush()


def print_help():
    log("Unified FPGA synthesizer frontend\r\n(c) Joppe Blondel - 2022\r\n")
    log(f"Usage: {sys.argv[0]} [ OPTIONS ] target ...")
    log("")
    log("Options:")
    log("  -h                 Show this help message")
    log("  -c <file>          Configuration file, defaults to project.cfg")

def main():
    # Parse arguments
    i = 1
    nextarg = None
    configpath = 'project.cfg'
    targets = []
    while i<len(sys.argv):
        if nextarg is not None:
            if nextarg=='config':
                configpath = sys.argv[i]
                nextarg = None
            else:
                nextarg = None
        elif sys.argv[i]=='-h':
            print_help()
            exit(0)
        elif sys.argv[i]=='-c':
            nextarg = 'config'
        else:
            targets.append(sys.argv[i])
        i += 1
    if nextarg is not None:
        log("ERROR: expected more arguments")
        exit(1)

    config = configparser.ConfigParser()
    config.read(configpath)

    subprocesses = []

    def sighandler(num, frame):
        if num==signal.SIGINT:
            log("\rStopping rbuild")
            for p in subprocesses:
                p.terminate()
            signal.alarm(4)
        elif num==signal.SIGALRM:
            log("Force killing subprocesses")
            for p in subprocesses:
                p.kill()
            exit(0)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGALRM, sighandler)

    for target in targets:

        log("Target", target)

        toolchain = config.get(f'target.{target}', 'toolchain', fallback='NONE')
        if toolchain=='NONE':
            log("ERROR: No toolchain specified for target")
            exit(1)
        
        try:
            exec(f"from remotesyn.toolchains.{toolchain} import do")
        except ImportError:
            log(f"ERROR: Unknown toolchain '{toolchain}'")
            exit(1)

        ret = do(config, target, log, subprocesses)

        if ret!=0:
            log("ERROR: toolchain returned with", ret)
            exit(ret)


if __name__=="__main__":
    main()