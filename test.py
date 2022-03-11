import base64
import datetime
import json
import os
import re

import requests


def init():
    os.makedirs('var/vpn-history/', exist_ok=True)
    os.makedirs('var/configs/', exist_ok=True)


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
    file_json = f"var/vpn-history/{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')}.json"
    with open(file_json, 'w+', encoding='utf-8') as file:
        json.dump(vpn_list, file)
    return vpn_list


def download_file(url: str, file_name: str):
    r = requests.get(url, allow_redirects=True)
    open(file_name, 'wb').write(r.content)


def save_vpn_config_file(vpn_config: dict, file_name: str):
    config_base64 = vpn_config['open_v_p_n__config_data__base64']
    open(file_name, 'wb').write(base64.b64decode(config_base64))


def run():
    array = file_to_array('var/www.vpngate.net.txt')
    save_vpn_config_file(r[0], f"var/configs/{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}")
    te = 1


if __name__ == '__main__':
    init()
    download_file('https://www.vpngate.net/api/iphone/', 'var/www.vpngate.net.txt')
    run()
