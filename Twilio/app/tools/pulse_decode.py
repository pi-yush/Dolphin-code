import soundcard as sc
import numpy as np
import base64
import typing
import sys
import audioop

def get_sink_by_name(name: str):
	for m in sc.all_microphones(include_loopback = True):
		print(m.id)
		if m.id.find(name) != -1:
			return m
	return None

def get_source_by_name(name: str):
	for m in sc.all_speakers():
		print(m.id)
		if m.id.find(name) != -1:
			return m
	return None


if __name__ == '__main__':
    with open(sys.argv[1] , 'rb') as f:
        data = f.read()

    data = audioop.ulaw2lin(data , 1)
    data = np.frombuffer(data , np.float32)
    speaker = get_source_by_name('alsa')
    with speaker.player(8000) as sp:
        sp.play(data)