import subprocess
import pathlib
from Levenshtein import distance
from string import printable
from random import choice


def ber(d1: bytes, d2: bytes) -> float:
    s1 = "".join(bin(i)[2:] for i in d1)
    s2 = "".join(bin(i)[2:] for i in d2)

    dist = distance(s2, s1)

    return dist/len(s1) * 100


def generate_data(size: int):
    return "".join(random.choice(printable) for _ in range(size)).encode('utf-8')


def filter_amr(wav_file: pathlib.Path):
    enc_amr_cmd = "ffmpeg -i {wav_file.unix()}"

def test(f1, f2):
    with open(f1, "rb") as f:
        d1 = f.read()

    with open(f2, "rb") as f:
        d2 = f.read()


    print(ber(d1, d2))

import sys

if __name__ == "__main__":
    test(sys.argv[1], sys.argv[2])
