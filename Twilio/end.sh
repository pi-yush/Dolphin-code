#!/bin/bash
kill -9 `ps aux | grep "uvicorn" | tr -s " " | cut -d " " -f 2 | head -n 1`