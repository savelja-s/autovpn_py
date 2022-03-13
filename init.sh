#!/bin/bash

mkdir -p var/log/
mkdir -p tmp
sudo apt install openvpn python3-setuptools python3-pip
pip install --no-cache-dir -r requirements.txt
