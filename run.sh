#!/bin/bash
cd $1
source .venv/bin/activate
python3 -m pip install -r requirements.txt >/dev/null 2>&1
nohup python3 route-prefix-builder.py >/dev/null 2>&1 &
deactivate
