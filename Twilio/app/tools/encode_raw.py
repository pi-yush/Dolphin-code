import pyaudio
from base64 import b64encode


p = pyaudio.PyAudio()

stream = p.open(
    format = pyaudio.get_format_from_width(1),
    channels = 1,
    rate = 8000,
    input = True,
    frames_per_buffer = 512,
    input_device_index = 9
)

while True:
    data = stream.read(512)
    print(f"[+] Data : {b64encode(data)}")