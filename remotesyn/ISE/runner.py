import threading
import shutil
import os
import time
import subprocess

def runner(threads, process, name):
    print(f" - executing {name}: ", end='', flush=True)
    p = subprocess.Popen(process, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threads.append(p)
    while p.poll() is None:
        print('.', end='', flush=True)
        time.sleep(2)
    res = p.returncode