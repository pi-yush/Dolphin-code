import dbus
import subprocess
import sys
import os
import signal
from pathlib import Path
import zlib
import base64
import itertools
import time
import smtplib
from twython import Twython

from coincurve import PrivateKey
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES

DELTA = 100

SINK_NAME = "<pulseaudio sink name>"

bus = dbus.SystemBus()

manager =  dbus.Interface(bus.get_object('org.ofono', '/'), 'org.ofono.Manager')
modems = manager.GetModems()

def enable_modem():
    os.system("/home/nsl8/ofono/test/enable-modem")

def main():
    if len(sys.argv) != 4:
        print(f"[!] Usage : {sys.argv[0]} <filesize> <bps> <num_tests>")
        exit(-1)

    bps = int(sys.argv[2])
    n = int(sys.argv[3])
    fileSize = int(sys.argv[1])

    to_be_done = progress(n, bps, fileSize)

    for i in to_be_done:
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
		file = str(file)
		file = file[file.find("/")+1:]
		num = int(file.split("_")[0])
		done_num.append(num)
	not_done_num = []
	for i in range(n):
		if not i in done_num:
			not_done_num.append(i)
	return not_done_num



def run_minimodem(filename, bps, timeout_val):
    return subprocess.Popen([f"timeout {timeout_val} /usr/bin/minimodem -q --rx {bps}"] ,
                        shell=True , stdout=subprocess.PIPE)

def close_minimodem(proc):
    proc.kill()

def check_disconnect(mgrs):
    for mgr in mgrs:
        calls = mgr.GetCalls()

        for _ , props in calls:
            return False
    return True

def process_recv_data(data, actual_data, aes_obj):
    data_chunks = data.split(b'=')                                                                                                                                  
    data_chunks = data_chunks[:-1]                                                                                                                                  
    print(data_chunks)                                                                                                                                              
    for i,chunk in enumerate(data_chunks):                                                                                                                            
        chunk += b"="                                                                                                                                                 
        print(f"Chunk: {chunk} Length of Chunk: {len(chunk)}")                                                                                                      
        if(len(chunk) == 28):                                                                                                                                       
            try:                                                                                                                                                    
                decoded_data = base64.b64decode(chunk)                                                                                                                
            except:                                                                                                                                             
                print(f"Could not decode chunk properly!")                                                                                                      
                continue
            print(f"[+] Decoded Content: {decoded_data}")
            decrypted_data = aes_obj.decrypt(decoded_data[:16])
            print(f"[+] Decrypted Content: {decrypted_data}")
            print(decrypted_data[0], decrypted_data[1:16], decoded_data[16:])                                                                                           
            if(zlib.crc32(decoded_data[:16]).to_bytes(4, byteorder = 'big') == decoded_data[16:]):                                                                  
                dec_str = decrypted_data[:16].decode('ascii')
                index = int(dec_str[0])
                print(f"Chunk {index} is correctly received!")                                                                                            
                actual_data[index] = decrypted_data[1:16]                                                                                              
            else:                                                                                                                                                   
                print(f"Chunk is corrupted! The checksum didn't match!")                                                                                          
        else:                                                                                                                                                       
            print(f"Chunk is corrupted! Length of chunk not expected!")                                                                                           

    print(f"[+] Actual Data : {actual_data}")
    return actual_data

def derive_key():
    r_key = PrivateKey.from_hex(os.urandom(32).hex())
    print("[+] Generating ECDH public part...")
    pub_key = r_key.public_key.format()
    sendable_data = pub_key + zlib.crc32(pub_key).to_bytes(4, byteorder = 'big')
    b64_data = base64.b64encode(sendable_data)
    print(f"[+] Public part {sendable_data.hex()} Length : {len(b64_data)}")
    send_pub_key = b''
    checksum = b''
    got_public = False
    while(True):
        mute_sink()
        proc = run_minimodem("hello", 16, 40)
        result = proc.communicate()[0]
        print(f"[+++]Received data before replacing new line : {result}")
        result = result.replace(b'\n',b'')
        print(f"[+++]Received data: {result}")
        if(result.count(b'=') >= 5 or got_public):
            break
        if(len(result) != 52):
            print("[+] Received Key's length incorrect!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data(8,"12345", 13)
            time.sleep(13 - (time.time() - temp_ts))
            mute_sink()
            continue
        try:
            decoded = base64.b64decode(result)
            checksum = decoded[33:]
            print(f"[+] Length of decoded data {len(decoded)} recv checksum : {checksum.hex()} calc_checksum :{zlib.crc32(result[:33]).to_bytes(4, byteorder = 'big').hex()}")
        except:
            print("[+] Unable to decode data!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data(8, "12345", 13)
            time.sleep(13 - (time.time() - temp_ts))
            mute_sink()
            continue
        if(zlib.crc32(decoded[:33]).to_bytes(4, byteorder = 'big') == checksum):
            print("[+] Successfully Received other party's ECDH public part!!")
            send_pub_key = decoded[:33]
            print(f"[+++] Received public part {send_pub_key.hex()}")
            got_public = True
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data(8,"======", 13)
            mute_sink()
            time.sleep(13 - (time.time() - temp_ts))
        else:
            print("[+] Cheksum incorrect!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data(8, "======", 13)
            mute_sink()
            time.sleep(13 - (time.time() - temp_ts))
    while(True):
        time.sleep(1)
        temp_ts = time.time()
        unmute_sink()
        send_data(8, b64_data.decode('ascii'), 69)
        time.sleep(69 - (time.time() - temp_ts))
        mute_sink()
        proc = run_minimodem("hello", 16, 7)
        result = proc.communicate()[0]
        result = result.replace(b'\n',b'')
        print(f"[+] Other party's acknoeledgement : {result}")
        if(result.count(b'=') >= 1):
            print("[+] Other party got the ECDH public part!!!")
            time.sleep(1)
            temp_ts = time.time()
            unmute_sink()
            send_data(8,"=====================================", 69)
            time.sleep(69 - (time.time() - temp_ts))
            mute_sink()
            break
 
    shared_key = r_key.ecdh(send_pub_key)
    print(f"[+++] Shared ECDH Key : {shared_key.hex()}")
    return shared_key

def calc_key(secret):
    salt = "this is a salt"
    key_material = PBKDF2(secret, salt.encode('ascii'), 32, count=1000)
    return key_material[:16], key_material[16:]

def run_test(modems , out_file , bps):
    mute_sink()
    mgrs = get_call_managers(modems)

    while not check_active_call(mgrs):
        continue

    secret = derive_key()
    key, IV = calc_key(secret)
    print(f"[+] Key : {key.hex()} IV : {IV.hex()}")
    aes_obj = AES.new(key, AES.MODE_ECB, IV)

    init_ts = time.time()
    timeout_val = 56 # delay from sender side + time to transmit data
    mute_sink()
    
    actual_data = [b'' for _ in range(0,5)] 
    data_left = True
    first = True
    missing = ["1" for _ in range(0,5)]
    send_timeout = 12
    while(data_left):
        proc = run_minimodem(out_file , bps, timeout_val)
        ts_after_data_recv = time.time()
        result = proc.communicate()[0]                                                                                                                              
        print(f"Result : {result}")
        if(result == b'' and not first):
            print(f"[+] String to be sent : {b64_resp_string.decode('ascii')}")                                                                                     
            unmute_sink()                                                                                                                                       
            print("[+] Sending ACK Info ...")                                                                                                                       
            send_data(16, b64_resp_string.decode('ascii'))                                                                                                      
            mute_sink()
            continue
        data = result
        first = False
        actual_data = process_recv_data(data, actual_data, aes_obj)
        for i in range(len(actual_data)):
            print(len(actual_data[i]))
            if(len(actual_data[i]) == 0):
                missing[i] = "1"
            else:
                missing[i] = "0"
        missing_str = "".join(itertools.chain(*missing))
        print(f"Missing : {missing_str}")
        if(missing_str == "00000"):
            print("[+] Data successfully received!")
            actual_data_str = b''.join(actual_data)
            actual_data_str = actual_data_str.decode('ascii')
            print(f"[+] Final Data string : {actual_data_str}")
            
            data_left = False
            resp = "============"
            time.sleep(1)
            unmute_sink()
            send_data(16, resp, send_timeout)
            mute_sink()
            continue
        else:
            resp_string = missing_str.encode('ascii') + zlib.crc32(missing_str.encode('ascii')).to_bytes(4, byteorder = 'big')
        b64_resp_string = base64.b64encode(resp_string)
        print(f"[+] Base64 Response String : {b64_resp_string}")
        print(f"[+] String to be sent : {b64_resp_string.decode('ascii')}")
        unmute_sink()
        print(f"[+] Time taken by receiver : {time.time() - ts_after_data_recv}")
        print(f"[+] Total processing time for first batch {time.time() - init_ts}")
        print("[+] Sending ACK Info ...")
        time.sleep(1)
        temp_ts = time.time()
        send_data(16, b64_resp_string.decode('ascii'), send_timeout)
        time.sleep(12 - (time.time() - temp_ts))
        mute_sink()
        timeout_val = 11*5

def send_data(bps, data, send_timeout):
    subprocess.run([f"timeout {send_timeout} bash -c \"echo '{data}' | minimodem --tx {bps}\""], shell=True )#, input=data)

def mute_sink():
    os.system(f"pactl {SINK_NAME} 1")

def unmute_sink():
    os.system(f"pactl {SINK_NAME} 0")

if __name__ == "__main__":
    main()
