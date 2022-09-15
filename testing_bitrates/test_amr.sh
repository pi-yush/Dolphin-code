#! /bin/bash
#set -xe

# Change the base_file name to test for different file sizes

set -e
base_file=./bible_1000.txt

bandwidths=("4.75" "5.15" "5.9" "6.7" "7.4" "7.95" "10.2" "12.2")
bitrates=("32" "64" "128" "256" "512" "1024" )


for bps in ${bitrates[@]}
do
    echo "[+] Testing for ${bps} bps"
    for bwd in ${bandwidths[@]};
    do
        cat $base_file | minimodem --tx $bps -f data_$bps.wav > /dev/null
        yes | ffmpeg -i data_$bps.wav -ar 8000 -ab ${bwd}k -ac 1 out.amr 2> /dev/null
        yes | ffmpeg -i out.amr -ar 32000 out_data_$bps.wav 2>/dev/null
        minimodem --rx $bps -f out_data_$bps.wav > out_char.txt 2> /dev/null

        val=$(python3 dol_ber.py $base_file out_char.txt)
        echo "   $bwd : $val% ber"
    done
done

echo "[+] Cleaning"
rm -v *.wav out_char.txt out.amr
