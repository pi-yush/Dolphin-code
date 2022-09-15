#!/usr/bin/python3
import dbus
import subprocess
import sys
import os
import signal
from pathlib import Path

DELTA = 100

bus = dbus.SystemBus()

manager =  dbus.Interface(bus.get_object('org.ofono', '/'), 'org.ofono.Manager')
modems = manager.GetModems()

def enable_modem():
    os.system("/home/nsl8/ofono/test/enable-modem")

def main():
    if len(sys.argv) != 4:
        print(f"[!] Usage : {sys.argv[0]} <fileSize> <bps> <num_tests>")
        exit(-1)

    bps = int(sys.argv[2])
    n = int(sys.argv[3])
    fileSize = int(sys.argv[1])

    # print(f"[+] Running {n} tests at {bps} bps at offset {off}")

    to_be_done = progress(n, bps, fileSize)

    for i in to_be_done:
        #os.system("/home/nsl1/ofono/test/enable-modem")
        file = f"data_{bps}_{fileSize}/{i}_{bps}.out"
        run_test(modems , file, bps)

def get_call_managers(modems):
    mgrs = []
    for path , _ in modems:
        print(f"[+] Path : {path}")
        mgrs.append(
            dbus.Interface(bus.get_object('org.ofono', path), 'org.ofono.VoiceCallManager')
        )
        return mgrs


def check_active_call(mgrs):
    for mgr in mgrs:
        calls = mgr.GetCalls()

        for _ , props in calls:
            state = props["State"]

            if state == "active":
                return True
    return False


def progress(n, bps, fileSize):
    global DELTA
    DELTA = fileSize*3/10
    working_directory = Path(f"data_{bps}_{fileSize}")
    working_directory.mkdir(parents=True, exist_ok=True)
    done_verified = []
    done = working_directory.glob('**/*')
    for file in done:
        if abs(file.stat().st_size - fileSize) > DELTA:
            file.unlink()
            continue
        done_verified.append(file)
    print(f"[+] {len(done_verified)} experiments already done out of {n}")
    done_num = []
    for file in done_verified:
        '''Assuming files are stored as <num>_<bps>.out'''
        file = str(file)
        file = file[file.find("/")+1:]
        num = int(file.split("_")[0])
        done_num.append(num)
    not_done_num = []
    for i in range(n):
        if not i in done_num:
            not_done_num.append(i)
    return not_done_num



def run_minimodem(filename , bps):
    enable_modem()
    #time.sleep(0.5)
    return subprocess.Popen([f"/usr/bin/minimodem --rx {bps} > {filename}"] ,
            shell=True , stderr=subprocess.DEVNULL)

def close_minimodem(proc):
    proc.kill()

def check_disconnect(mgrs):
    for mgr in mgrs:
        calls = mgr.GetCalls()

        for _ , props in calls:
            return False
    return True


def run_test(modems , out_file , bps):
    mgrs = get_call_managers(modems)

    while not check_active_call(mgrs):
        continue

    proc = run_minimodem(out_file , bps)

    while not check_disconnect(mgrs):
        continue
    print(f"[+] Minimodem PID : {proc.pid}")
    os.system("pkill -f minimodem")
    #close_minimodem(proc)

if __name__ == "__main__":
    main()
