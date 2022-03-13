#!/bin/bash

mkdir -p var/vpn-history/
mkdir -p var/configs/
mkdir -p var/logs/
sudo apt install openvpn python3-setuptools python3-pip
pip install --no-cache-dir -r requirements.txt
