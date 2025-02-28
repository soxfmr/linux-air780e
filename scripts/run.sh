#!/bin/bash

. venv/bin/activate

python main.py read -p "$1" --delete-after-read