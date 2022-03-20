import base64
import datetime
import json
import logging
import os
import random
import re
import requests
from simplejson import JSONDecodeError


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[38;5;196m'  # 91m
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    C_BLUE = '\033[38;5;21m'
    C_GREEN = '\033[38;5;46m'
    C_YELLOW = '\033[38;5;226m'
    C_87 = '\033[38;5;87m'


# def colors_16(color_):
#     return ("\033[2;{num}m {num} \033[0;0m".format(num=str(color_)))
#
#
# def colors_256(color_):
#     num1 = str(color_)
#     num2 = str(color_).ljust(3, ' ')
#     if color_ % 16 == 0:
#         return (f"\033[38;5;{num1}m {num2} \033[0;0m\n")
#     else:
#         return (f"\033[38;5;{num1}m {num2} \033[0;0m")
#
#
# print("The 16 colors scheme is:")
# print(' '.join([colors_16(x) for x in range(30, 38)]))
# print("\nThe 256 colors scheme is:")
# print(' '.join([colors_256(x) for x in range(256)]))
CONFIG_INFO = {
    'host_name': '- Host name: ',
    'country_long': '- Country: ',
    'country_short': '- Country CODE: ',
    'i_p': '- IP: ',
    'ping': '- Ping: ',
    'speed': '- Speed: ',
    'total_users': '- Total users: ',
    'operator': '- Operator: ',
}


class VPNConfig(object):
    tmp_dir_path: str
    vpn_server_list_url: str
    country_code: str
    config_path: str
    current_index: int = 0

    def __init__(self, tmp_dir_path, vpn_server_list_url, country_code=None, is_rand=False):
        self.tmp_dir_path = tmp_dir_path
        self.vpn_server_list_url = vpn_server_list_url
        self.country_code = country_code
        self.is_rand = is_rand
        self.config_path = f'{tmp_dir_path}autovpn_config.ovpn'
        self.init_config()

    def save_config_file(self, vpn_config: dict):
        open(self.config_path, 'wb').write(
            base64.b64decode(vpn_config['open_v_p_n__config_data__base64'])
        )

    def init_config(self):
        vpn_list = self.get_vpn_list()
        if vpn_list is None or not len(vpn_list):
            msg = 'Not init index.'
            print(f'{bcolors.FAIL}{msg}{bcolors.ENDC}')
            raise RuntimeError(msg)
        count = len(vpn_list)
        if self.is_rand:
            current_index = random.randint(0, count - 1)
        else:
            next_index = self.current_index + 1
            current_index = 0 if count < next_index else next_index
        config = vpn_list[current_index]
        logging.info('INIT CONFIG:' + str(config))
        self.save_config_file(config)
        print(f'{bcolors.C_GREEN}INIT CONFIG:{bcolors.ENDC}')
        for field in CONFIG_INFO:
            value = config[field] if field != 'speed' else f'{round(int(config[field]) / (1024 * 1024), 2)} Mb'
            print(f'{bcolors.C_GREEN}{CONFIG_INFO[field]}{value}{bcolors.ENDC}')

    def get_vpn_list(self):
        file_dir = f'{self.tmp_dir_path}vpn-history'
        os.makedirs(file_dir, exist_ok=True)
        interval = divmod(datetime.datetime.now().minute, 10)[0]
        file_path = f"{file_dir}/{datetime.datetime.now().strftime('%Y-%m-%d_%H_')}{interval}.json"
        if os.path.isfile(file_path):
            print(f'{bcolors.C_87}LOAD FILE with cache{bcolors.ENDC}')
            vpn_list = json.load(open(file_path))
        else:
            print(f'{bcolors.OKGREEN}UPLOAD FILE with {self.vpn_server_list_url}{bcolors.ENDC}')
            response = requests.get(self.vpn_server_list_url, allow_redirects=True)
            vpn_list = []
            for vpn_server in response.content.splitlines():
                vpn_server = vpn_server.decode('utf-8')
                if vpn_server.startswith('*'):
                    continue
                if vpn_server.startswith('#'):
                    h = [re.sub(r'(?<!^)(?=[A-Z])', '_', name.lstrip('#').strip()).lower() for name in
                         vpn_server.split(',')]
                    continue
                vpn_info = {h[idx]: item for idx, item in enumerate(vpn_server.split(','))}
                vpn_list.append(vpn_info)
            self.current_index = -1
        vpn_list.sort(key=lambda item: item['speed'], reverse=True)
        save_json(vpn_list, file_path)
        if self.country_code:
            filter(lambda item: item['country_short'] == self.country_code, vpn_list)
        return vpn_list


def track_my_ip() -> str:
    list_urls = [
        'https://checkip.amazonaws.com',
        'https://api.ipify.org',
        'https://ident.me',
        'http://ipgrab.io',
        'http://ipecho.net/plain',
        'https://icanhazip.com',
        'http://ip.jsontest.com',
        'http://ip.42.pl/raw',
        'http://jsonip.com',
        'https://ipapi.co/ip',
        'http://myexternalip.com/raw',
        'https://wtfismyip.com/text',
        'http://ipinfo.io/json',
    ]
    url = list_urls[random.randint(0, len(list_urls) - 1)]
    response = requests.get(url=url)
    response.encoding = 'UTF-8'
    try:
        response = response.json()
        ip = response['ip']
    except JSONDecodeError:
        response = response.text
        ip = response.strip()
    logging.info('CURRENT IP:' + str(response))
    return ip


def save_json(data, file_json: str):
    with open(file_json, 'w+', encoding='utf-8') as file:
        json.dump(data, file)
