#! /bin/env python3
import subprocess
import sys
import dbus
from time import sleep
import signal, os
from refresh import enable_modem, place_call, hangup_call
import zlib
import base64
import itertools
import time

from coincurve import PrivateKey
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES

SERV_NO = "<Server's smartphone number>"
SINK_NAME = "<pulseaudio sink name>"

bus = dbus.SystemBus()
manager =  dbus.Interface(bus.get_object('org.ofono', '/'), 'org.ofono.Manager')
modems = manager.GetModems()

def enable_modem():
    os.system("/path/to/ofono/github/source/test/enable-modem")


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




def ctrlC_hit(signalNumber, frame):
	hangup_call()
	exit(1)

def send_data(data , bps, send_timeout):
    # print(data, bps)
    subprocess.run([f"timeout {send_timeout} bash -c \"echo '{data}' | minimodem --tx {bps}\""], shell=True )#, input=data)

def recv_data(bps, timeout_val):
    #processing time + reverse transmission time
    #timeout_val = 3 + 6
    proc = subprocess.Popen([f'timeout {timeout_val} minimodem -q --rx {bps}'], shell=True, stdout=subprocess.PIPE)
    result = proc.communicate()[0]
    result = result.replace(b'\n', b'')
    return result

def read_file(filename):
    with open(filename , "r") as f:
        return f.read()

def process_data(data, aes_obj):
    chunks, chunk_size = len(data), 15
    #print(chunks, chunk_size)
    data_chunks = [ data[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
    data = b''
    encoded_data_chunks = [b'' for _ in range(0,5)]
    for i,chunk in enumerate(data_chunks):
        chunk = str(i) + chunk
        print(chunk)

        chunk = aes_obj.encrypt(chunk)
        print(f"Encrypted Chunk : {chunk}")

        temp_chunk = (chunk + zlib.crc32(chunk).to_bytes(4, byteorder = 'big'))
        b64_chunk_data = base64.b64encode(temp_chunk)
        encoded_data_chunks[i] = b64_chunk_data
        #data += b64_chunk_data
    return encoded_data_chunks

def sendable_data(encoded_data_chunks, indexes):
    data = [encoded_data_chunks[i] for i in range(len(encoded_data_chunks)) if indexes[i] == '1']
    data = b''.join(data)
    data = data.decode('ascii')
    print("Data to be sent : " + data)
    print(len(data))
    return data

def derive_key():
    s_key = PrivateKey.from_hex(os.urandom(32).hex())
    print("[+] Generating ECDH public part...")
    pub_key = s_key.public_key.format()
    sendable_data = pub_key + zlib.crc32(pub_key).to_bytes(4, byteorder = 'big')
    print(f"Length of data before encoding : {len(sendable_data)}")
    b64_data = base64.b64encode(sendable_data)
    print(f"[+] Sending public part {b64_data} Length : {len(b64_data)}")
    recv_pub_key = b''
    got_public = False
    while(True):
        time.sleep(1)
        temp_ts = time.time()
        unmute_sink()
        send_data(b64_data.decode('ascii'), 16, 39)
        time.sleep(39 - (time.time() - temp_ts))
        mute_sink()
        result = recv_data(8, 14)
        print(f"[+] Other party's acknoeledgement : {result}")
        if(result.count(b'=') >= 1):
            print("[+] Other party got the ECDH public part!!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data("=====================================", 16, 39)
            time.sleep(39 - (time.time() - temp_ts))
            mute_sink()
            break
    while(True):
        mute_sink()
        result = recv_data(8, 70)
        print(f"[+++]Received data: {result}")
        if(result.count(b'=') >= 5 or got_public):
            print("[+] ECDH Key exchange Done!")
            break
        if(len(result) != 52):
            print("[+] Received Key's length incorrect!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data("12345", 16, 6)
            time.sleep(6 - (time.time() - temp_ts))
            mute_sink()
            continue
        checksum = result[33:]
        try: 
            decoded = base64.b64decode(result)
            checksum = decoded[33:]
        except:
            print("[+] Unable to decode data!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data("12345", 16, 6)
            time.sleep(6 - (time.time() - temp_ts))
            mute_sink()
            continue

        if(zlib.crc32(decoded[:33]).to_bytes(4, byteorder = 'big') == checksum):
            print("[+] Successfully Received other party's ECDH public part!!")
            recv_pub_key = decoded[:33]
            print(f"[+++] Received public part {recv_pub_key.hex()}")
            got_public = True
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data("======", 16, 6)
            time.sleep(6 - (time.time() - temp_ts))
            mute_sink()
        else:
            print("[+] Cheksum incorrect!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data("12345", 16, 6)
            time.sleep(6 - (time.time() - temp_ts))
            mute_sink()
      
    shared_secret = s_key.ecdh(recv_pub_key)
    print(f"[+++] Shared ECDH Key : {shared_secret.hex()}")
    unmute_sink()
    return shared_secret

def calc_key(secret):
    salt = "this is a salt"
    key_material = PBKDF2(secret, salt.encode('ascii'), 32, count=1000)
    return key_material[:16], key_material[16:]

def run_test(data, bps, contact_number):
    print("[+] Running test")
    mgrs = get_call_managers(modems)

    #while not check_active_call(mgrs):
    #    continue
    #print(f"[+] Call received by the other party!!")
    
    enable_modem()

    #key = derive_key()

    unmute_sink()
    #sleep(1)
    place_call(contact_number)
    while not check_active_call(mgrs):
        continue
    print(f"[+] Call received by the other party!!")
    secret = derive_key()
    key, IV = calc_key(secret)
    print(f"[+] Key : {key.hex()} IV : {IV.hex()}")
    aes_obj = AES.new(key, AES.MODE_ECB, IV)
    #sleep(4)
    print("[+] Sending data ...")
    data_left = True
    corrupted = True
    indexes = ['1' for _ in range(0,5)]
    chunk_array = process_data(data, aes_obj)
    timeout_val = 13
    send_timeout = 5*11
    while(data_left):
        unmute_sink()
        data_to_send = sendable_data(chunk_array, indexes) 
        time.sleep(1)
        ts_before_send = time.time()
        send_data(data_to_send , bps, send_timeout)
        time.sleep(55 - (time.time() - ts_before_send))
        mute_sink()
        #indexes = ['0' for _ in range(0,5)]
        corrupted = True
        while (corrupted):
            result = recv_data(16, timeout_val)
            data_left, corrupted, indexes = process_result(result, indexes)
            count = ["1" for i in range(len(indexes)) if indexes[i] == "0"]
            timeout_val = len(count)*11 + 13
            send_timeout = ((5-len(count))*11)
            if(corrupted):
                print(f"[+] Sending data again! {data_to_send}")
                print(f"[+] Recalculated timeout val {timeout_val}")
                unmute_sink()
                time.sleep(1)
                temp_ts = time.time()
                send_data(data_to_send, bps, send_timeout)
                time.sleep(55 - (time.time() - temp_ts))
                mute_sink()
    unmute_sink()
    sleep(1)
    hangup_call()
    #sleep(5)

def process_result(data, indexes):
    print(f"Received Data: {data}")
    missing_index = []
    if (data.count(b'=') >= 1):
        return False, False, indexes
    try:
        decoded_data = base64.b64decode(data)
        print(f"Decoded data : {decoded_data}")
        index_string = decoded_data[:5]
        #index_string = index_string.decode('ascii')
        received_checksum = decoded_data[5:]
        if(zlib.crc32(decoded_data[:5]).to_bytes(4, byteorder = 'big') == received_checksum):
            #index_string = decoded_data[:5]
            index_string = index_string.decode('ascii')
            missing_index[:0] = index_string
            print(f"[+] Missing Indexes {missing_index}")
            return True, False, missing_index
        else:
            print("[+] Checksum Mismatch!!")
            return True, True, indexes
    except base64.binascii.Error as err:
        print(f"Corrupted data!")
        return True, True, indexes
	
    #chunks, chunk_size = len(data), int(len(data)/5)
    #print(chunks, chunk_size)

def mute_sink():
    os.system(f"pactl set-sink-mute {SINK_NAME} 1")

def unmute_sink():
    os.system(f"pactl set-sink-mute {SINK_NAME} 0")

def main():
    if len(sys.argv) != 5:
        print(f"[!] Usage : {sys.argv[0]} <data_file> <size> <bps> <num_test>")
        exit(1)
    signal.signal(signal.SIGINT, ctrlC_hit)
    data = read_file(sys.argv[1])[:int(sys.argv[2])]
    print(len(data))
    # data = "Hello world"
    # print(data, len(data))
    bps = int(sys.argv[3])
    n = int(sys.argv[4])
    for _ in range(n):
        run_test(data , bps, SERV_NO)
        sleep(1)

if __name__ == "__main__":
    main()
