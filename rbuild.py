#!/usr/bin/env python

import remotesyn
import remotesyn.ISE as ISE

import configparser
import signal
import time

threads = []

def sighandler(sig, frame):
    print("\nCRTL-C: stopping threads")

    for t in threads:
        t.stop();

    exit(0);

if __name__=="__main__":
    signal.signal(signal.SIGINT, sighandler)

    config = configparser.ConfigParser()
    config.read("project.cfg")

    # Test local build
    copy = remotesyn.copy_local(config)
    synth = ISE.synth(config, copy, 'default')
    threads.append(synth)

    needed_files = synth.needed_files()
    print(needed_files)

    synth.start()

    looping = True
    while looping:
        time.sleep(1)
        looping = False
        for t in threads:
            if t.running:
                looping = True