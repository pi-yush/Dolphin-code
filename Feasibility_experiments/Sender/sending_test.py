#! /bin/env python3
import subprocess
import sys
import dbus
from time import sleep
import signal, os
from refresh import enable_modem, place_call, hangup_call, wait_for_call_to_pick

RECV_NO="<Reciever's phone number>"

def ctrlC_hit(signalNumber, frame):
	hangup_call()
	exit(1)

def send_data(data , bps):
    # print(data, bps)
    subprocess.run([f'echo "{data}" | minimodem --tx {bps}'], shell=True )#, input=data)

def read_file(filename):
    with open(filename , "r") as f:
        return f.read()

def process_data(data):
    return data

def run_test(data, bps, contact_number):
    print("[+] Running test")
    enable_modem()
    sleep(1)
    place_call(contact_number)
    while not wait_for_call_to_pick():
    	pass
    sleep(2)
    print("[+] Sending data ...")
    send_data(process_data(data) , bps)
    sleep(1)
    hangup_call()
    sleep(5)

def main():
    if len(sys.argv) != 5:
        print(f"[!] Usage : {sys.argv[0]} <data_file> <size> <bps> <num_test>")
        exit(1)
    signal.signal(signal.SIGINT, ctrlC_hit)
    data = read_file(sys.argv[1])[:int(sys.argv[2])]
    # data = "Hello world"
    # print(data, len(data))
    bps = int(sys.argv[3])
    n = int(sys.argv[4])
    for _ in range(n):
        run_test(data , bps, RECV_NO)
        sleep(1)

if __name__ == "__main__":
    main()
