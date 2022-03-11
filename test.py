import datetime
import json
import os
import re

import requests


def init():
    os.makedirs('var/vpns/', exist_ok=True)


def file_to_array(file_name: str) -> list:
    vpn_list = []
    with open(file_name) as file:
        for line in file:
            if line.startswith('*'):
                continue
            if line.startswith('#'):
                h = [re.sub(r'(?<!^)(?=[A-Z])', '_', name.lstrip('#').strip()).lower() for name in line.split(',')]
                continue
            vpn_info = {h[idx]: item for idx, item in enumerate(line.split(','))}
            vpn_list.append(vpn_info)
    file_json = f"var/vpns/{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')}.json"
    with open(file_json, 'w+', encoding='utf-8') as file:
        json.dump(vpn_list, file)
    return vpn_list


def download_file(url: str, file_name: str):
    r = requests.get(url, allow_redirects=True)
    open(file_name, 'wb').write(r.content)


def run():
    r = file_to_array('var/www.vpngate.net.txt')
    te = 1


if __name__ == '__main__':
    init()
    download_file('https://www.vpngate.net/api/iphone/', 'var/www.vpngate.net.txt')
    run()
