#!/bin/sh
pipenv install
nohup pipenv run python3 route-prefix-builder.py >/dev/null 2>&1 &

