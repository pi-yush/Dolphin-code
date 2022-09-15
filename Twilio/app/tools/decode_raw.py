import pyaudio
import sys
import audioop

if len(sys.argv) != 2:
	print("[+] Usage : test.py <raw_data_file>")
	exit(-1)

p = pyaudio.PyAudio()

stream = p.open(
		format = pyaudio.get_format_from_width(2),
		channels = 1,
		rate = 8000,
		output = True,
		# output_device_index = 8
	)

with open(sys.argv[1] , 'rb') as f:
	data = f.read()

# data = audioop.ulaw2lin(data , 2)

stream.write(data)

stream.close()

p.terminate()