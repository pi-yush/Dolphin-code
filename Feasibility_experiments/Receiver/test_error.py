import typing
from Levenshtein import distance
from pathlib import Path
import sys
from tqdm import tqdm

def ber(d1 : bytes , d2 : bytes) -> float:

    s1 = "".join(bin(i)[2:] for i in d1)
    s2 = "".join(bin(i)[2:] for i in d2)


    dist = distance(s2, s1)
    #print(dist)
    # print((float(dist)/float(len(s1)))*100)
    return (dist / len(s1)) * 100

def summarize(inp_dir : Path , size : int):
    with open("./bible.txt" , "rb") as f:
        d1 = f.read(size)

    def f1(p : Path) :
        with p.open(mode = "rb") as f:
            d2 = f.read()
        return ber(d1 , d2)

    inp_files = list(inp_dir.glob("*.out"))
    bers = list(map(f1 , tqdm(inp_files , total = len(inp_files))))

    return sum(bers)/len(bers)

if __name__ == "__main__":
    final_summary = {}
    if len(sys.argv)==3 and sys.argv[1] == "files":
        tar_dir = Path(sys.argv[2])
        size = int((sys.argv[2]).split("_")[-1])
        data_files = tar_dir.glob("**/*")
        for f in data_files:
            if f.name == "./bible.txt":
                continue
            with open("./bible.txt" , "rb") as t:
                d1 = t.read(size)
            with f.open(mode = "rb") as l:
                d2 = l.read()
            print(f"{f.name} {ber(d1,d2)}")
        print(f"Overall: {summarize(Path(sys.argv[2]), size)}")
        exit(1)
    data_root = Path(sys.argv[1])
    bps_set = set()
    size_set = set()

    for data_dir in data_root.glob("data_*"):
        print(f"\n[+] Summarizing directory {data_dir.name}\n")
        bps , size = map(int  , data_dir.name.split("_")[1:])
        bps_set.add(bps)
        size_set.add(size)
        mean_ber = summarize(data_dir , size)

        final_summary[(bps , size)] = mean_ber
    bps_set = sorted(bps_set)
    size_set = sorted(size_set)
    print("-----------------------Summary-------------------------")
    print("                       Bit-Rate                        ")
    print("Bytes " , end="\t")
    for e in bps_set:
        print(f"{e} " , end="\t")
    print("")

    for i in size_set:
        print(f"{i} " , end="\t")
        for j in bps_set:
            if (j , i) in final_summary:
                print(f"{round(final_summary[(j , i)], 2)}%" , end="\t")
            else:
                print("-" , end="\t")
        print("")

