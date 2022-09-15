#! /bin/bash

cd ./app
python tools/setup_config.py
cd ..
docker build -t dolphin_twillio .
