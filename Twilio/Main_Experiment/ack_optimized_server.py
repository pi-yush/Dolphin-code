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
import crc8
import requests

import random
import string

DELTA = 100

#bps_timeout = 10
#ack_timeout = 12
n_chunks = 6
data_len = 72
len_chunk = 20
checksum_index = 13

bus = dbus.SystemBus()

manager =  dbus.Interface(bus.get_object('org.ofono', '/'), 'org.ofono.Manager')
modems = manager.GetModems()

def enable_modem():
    os.system("/home/nsl8/ofono/test/enable-modem")

def main():
    if len(sys.argv) != 6:
        print(f"[!] Usage : {sys.argv[0]} <filesize> <bps> <num_tests> <bps_timeout> <ack_timeout>")
        exit(-1)

    bps = int(sys.argv[2])
    n = int(sys.argv[3])
    bps_timeout = int(sys.argv[4])
    ack_timeout = int(sys.argv[5])
    fileSize = int(sys.argv[1])

    # print(f"[+] Running {n} tests at {bps} bps at offset {off}")

    to_be_done = progress(n, bps, fileSize)
    no_of_iterations = int(fileSize/data_len)
    print(f"no of iterations : {no_of_iterations}")
    init_ts = time.time()
    for i in range(0,no_of_iterations):
        #os.system("/home/nsl1/ofono/test/enable-modem")
        file = f"data_{bps}_{fileSize}/{i}_{bps}.out"
        run_test(modems , file, bps, bps_timeout, ack_timeout)
    print(f"Total time to download {no_of_iterations*100} bytes is {time.time()-init_ts}")
    #os.system("pulseaudio -k")

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



def run_minimodem(filename, bps, timeout_val):
    #enable_modem()
    #time.sleep(0.5)
    #timeout_val = 30 + 17.5 # delay from sender side + time to transmit data
    #return subprocess.Popen([f"timeout {timeout_val} /usr/bin/minimodem -q --rx {bps} > {filename}"] ,
    #        shell=True , stderr=subprocess.PIPE, stdout=subprocess.PIPE)
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

def process_recv_data(data, actual_data):
    data_chunks = data.split(b'=')                                                                                                                                  
    data_chunks = data_chunks[:-1]                                                                                                                                  
    print(data_chunks)                                                                                                                                              
    for i,chunk in enumerate(data_chunks):                                                                                                                            
        #print(f"Looking at Chunk {i}")                                                                                                                                
        chunk += b"="                                                                                                                                                 
        #decoded_data = base64.b64decode(chunk)                                                                                                                     
        print(f"Chunk: {chunk} Length of Chunk: {len(chunk)}")                                                                                                      
        if(len(chunk) == len_chunk):                                                                                                                                       
            try:                                                                                                                                                    
                decoded_data = base64.b64decode(chunk)                                                                                                                
            except:                                                                                                                                             
                print(f"Could not decode chunk properly!")                                                                                                      
                continue
            print(decoded_data)
            crc_obj = crc8.crc8()
            crc_obj.update(decoded_data[:checksum_index])
            print(decoded_data[0], decoded_data[1:checksum_index], decoded_data[checksum_index:]) 
            if(crc_obj.digest() == decoded_data[checksum_index:]):
            #if(zlib.crc32(decoded_data[:checksum_index]).to_bytes(4, byteorder = 'big') == decoded_data[checksum_index:]):                                                         
                dec_str = decoded_data[:checksum_index].decode('ascii')
                index = int(dec_str[0])
                print(f"Chunk {index} is correctly received!")                                                                                            
                #actual_data += decoded_data[:16]                                                                                                                   
                actual_data[index] = decoded_data[1:checksum_index]                                                                                              
            else:                                                                                                                                                   
                print(f"Chunk is corrupted! The checksum didn't match!")                                                                                          
        else:                                                                                                                                                       
            print(f"Chunk is corrupted! Length of chunk not expected!")                                                                                           

    print(f"[+] Actual Data : {actual_data}")
    return actual_data

def check_call():
    time.sleep(0.001)
    r = requests.get("http://localhost:8000/status")
    return r.json()["status"]


def run_test(modems , out_file , bps, bps_timeout, ack_timeout):
    mute_sink()
    mgrs = get_call_managers(modems)

    while not check_call():
        continue
    init_ts = time.time()
    timeout_val = bps_timeout*n_chunks + 1 # delay from sender side + time to transmit data
    mute_sink()
    print(f"[+] bps_timeout : {bps_timeout} ack_timeout : {ack_timeout}")
    #enable_modem()
    #proc = run_minimodem(out_file , bps, timeout_val)
    #result = proc.communicate()[0]
    #print(f"Result : {result}")

    #while not check_disconnect(mgrs):
    #    continue
    #print(f"[+] Minimodem PID : {proc.pid}")
    #os.system("pkill -f minimodem")
    actual_data = [b'' for _ in range(0,n_chunks)] 
    #with open (out_file, "rb") as myf    #    data=myfile.readline()
    #print(data)
    #data = result
    data_left = True
    first = True
    missing = ["1" for _ in range(0,n_chunks)]
    send_timeout = ack_timeout
    ack_lost_timeout = bps_timeout*n_chunks + 1
    while(data_left):
        proc = run_minimodem(out_file, bps, ack_lost_timeout)
        proc1 = run_minimodem(out_file , bps, timeout_val)
        ts_after_data_recv = time.time()
        result = proc1.communicate()[0]
        if(result.count(b'*') >=1):
            result.replace(b'*',b'')
            proc.kill()
            ack_lost_timeout = timeout_val
        else:
            result = proc.communicate()[0]
            #temp = result.split('=')
            #result = temp[0] + b'='
        print(f"Result : {result}")
        if(result == b'' and not first):
            print(f"[+] String to be sent : {b64_resp_string.decode('ascii')}")                                                                                     
            unmute_sink()                                                                                                                                       
            print("[+] Sending ACK Info ...")
            temp_ts = time.time()
            fname = gen_file_name()
            send_data(64, b64_resp_string.decode('ascii'), send_timeout, fname)
            send_twilio(fname)
            time.sleep(send_timeout - (time.time() - temp_ts))                                                                                                      
            mute_sink()
            continue
        data = result
        first = False
        actual_data = process_recv_data(data, actual_data)
        for i in range(len(actual_data)):
            print(len(actual_data[i]))
            if(len(actual_data[i]) == 0):
                missing[i] = "1"
            else:
                missing[i] = "0"
        #missing = ["1" for i in range(len(actual_data)) if actual_data[i] == b'']
        missing_str = "".join(itertools.chain(*missing))
        print(f"Missing : {missing_str}")
        match_str = "0"*n_chunks
        if(missing_str == match_str):
            print("[+] Data successfully received!")
            actual_data_str = b''.join(actual_data)
            actual_data_str = actual_data_str.decode('ascii')
            print(f"[+] Final Data string : {actual_data_str}")
            ## EMAIL SENDING CODE
            '''s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login('h4ck1ngn1nj44@gmail.com', "loop@123")
            send_list = ['sambuddho@iiitd.ac.in', 'mukulika@iiitd.ac.in', 'rishi17260@iiitd.ac.in', 'kartikey17242@iiitd.ac.in', 'devashishg@iiitd.ac.in', 'piyushs@iiitd.ac.in']
            msg = 'Subject: If you received this => Dolphins are communicating. Congrats!\n\n'
            msg = msg + actual_data_str
            for item in send_list:
                s.sendmail('h4ck1ngn1nj44@gmail.com', item, msg)
                time.sleep(3)
            '''

            ## TWITTER CODE
            #twitter = Twython('JfmTJu6FQ7wafo1YE4yUsPtfN','r38SaxOTEiS2wDvhppv0HKVcowCQHDyI5MLEnTEaPcjGFmgHjg','1342499899451961344-LYI23ywJjnV7LYcJReyeYSZH2z3ugo','VCla7obvKjwUwuT655902XanfSOX14ZgFRxLAtm2CUNUL')
            #twitter.update_status(status = actual_data_str)

            data_left = False
            resp = "==="
            #resp_string = resp.encode('ascii')
            time.sleep(1)
            unmute_sink()
            temp_ts = time.time()
            fname = gen_file_name()
            send_data(64, resp, send_timeout, fname)
            send_twilio(fname)
            if ((send_timeout - (time.time() - temp_ts)) > 0):
                time.sleep(send_timeout - (time.time() - temp_ts))
            mute_sink()
            print(f"[--] Total time to transfer {n_chunks*20} bytes reliably : {time.time()-init_ts}")
            continue
            #resp_string = resp.encode('ascii') + zlib.crc32(resp.encode('ascii')).to_bytes(4, byteorder = 'big')
        else:
            ack_bit_string = '0b' + missing_str
            ack_byte = int(ack_bit_string, 2).to_bytes(1, 'big')
            resp_string = ack_byte*3
            #resp_string = missing_str.encode('ascii') + zlib.crc32(missing_str.encode('ascii')).to_bytes(4, byteorder = 'big')
        b64_resp_string = base64.b64encode(resp_string)
        print(f"[+] Base64 Response String : {b64_resp_string}")
        print(f"[+] String to be sent : {b64_resp_string.decode('ascii')}")
        unmute_sink()
        print(f"[+] Time taken by receiver : {time.time() - ts_after_data_recv}")
        print(f"[+] Total processing time for first batch {time.time() - init_ts}")
        print("[+] Sending ACK Info ...")
        time.sleep(1)
        temp_ts = time.time()
        fname = gen_file_name()
        send_data(64, b64_resp_string.decode('ascii'), send_timeout, fname)
        send_twilio(fname)
        time.sleep(send_timeout - (time.time() - temp_ts))
        mute_sink()
        count = ["1" for i in range(len(actual_data)) if actual_data[i] == b'']
        #timeout_val = 11*5
        print(f"[+] Count {count} Length of count {len(count)}")
        timeout_val = bps_timeout*len(count) + 1

    #result = proc.communicate()[0]
    #print(result)

    #close_minimodem(proc)

def gen_file_name():
    return ''.join(random.sample(string.ascii_lowercase,5)) + '.wav'

def send_twilio(fname):
    os.system(f"curl -X POST localhost:8000/send/{fname}")
    #requests.post("http://localhost:8000/send/out.wav")

def send_data(bps, data, send_timeout, fname):
    subprocess.run([f"timeout {send_timeout} bash -c \"echo -n '{data}' | minimodem --tx {bps} -f ~/twilio/{fname}\""], shell=True )#, input=data)

def mute_sink():
    pass
    #os.system("pactl set-sink-mute bluez_sink.4C_02_20_14_6C_76.headset_audio_gateway 1")

def unmute_sink():
    pass
    #os.system("pactl set-sink-mute bluez_sink.4C_02_20_14_6C_76.headset_audio_gateway 0")

if __name__ == "__main__":
    main()
