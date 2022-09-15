from make_call import make_call
from pprint import pprint as pp
from pathlib import Path
import subprocess
import time
import argparse
import typing

from twilio.rest import Client

from Config import config
import requests
import os

def run_minimodem(bps: int , filepath : Path):
    filepath = filepath.as_posix()
    return subprocess.Popen([f"/usr/bin/minimodem --rx {bps} -R 8000 > {filepath}"] , shell=True , stderr=subprocess.DEVNULL)

def check_call_status(sid):
    client = Client(
        config["twilio_sid"],
        config["twilio_auth"]
    )
    call = client.calls(sid).fetch()
    print(f"[!] status : {call.status}\t" , end='\r')

    return call.status == "in-progress"

def run_test(bps: int , filepath: Path):
    call_sid = make_call().sid
    print(f"[+] Call_sid : {call_sid}")

    while not check_call_status(call_sid):
        continue

    print(f"\n[+] Running test")

    run_minimodem(bps , filepath)

    while check_call_status(call_sid):
        continue

    time.sleep(0.5)
    os.system("pkill -f minimodem")

    print(f"\n[+] Test complete")

def run_tests(bps: int , nums: int , dirpath: Path):
    dirpath.mkdir(parents=True , exist_ok=True)
    for n in range(nums):
        filepath = dirpath / f"{n}_{bps}.out"
        if filepath.exists():
            continue
        run_test(bps , filepath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "bps" , help = "The bps that minimodem will listen on" , type = int
    )
    parser.add_argument(
        "-n" , "--num" , help = "The number of tests to run" , type = int , default = 1
    )
    parser.add_argument(
        "-o" , "--output_dir" , help = "The directory where all the results will be stored",
        type = Path , default = Path("Results")
    )
    args = parser.parse_args()
    run_tests(args.bps , args.num , args.output_dir)
