#!/usr/bin/env python3

import base64
import datetime
import json
import os
import random
import re
import signal
import subprocess
import sys
import time
import argparse
import requests
import logging
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


#
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
# ROOT_DIR: str = os.path.dirname(__file__) + '/'
ROOT_DIR: str = '/'
logging.basicConfig(filename=f'{ROOT_DIR}var/log/autovpn_py.log',
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)


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


def get_vpn_list(url: str):
    resp = requests.get(url, allow_redirects=True)
    vpn_list = []
    for line in resp.content.splitlines():
        line = line.decode('utf-8')
        if line.startswith('*'):
            continue
        if line.startswith('#'):
            h = [re.sub(r'(?<!^)(?=[A-Z])', '_', name.lstrip('#').strip()).lower() for name in line.split(',')]
            continue
        vpn_info = {h[idx]: item for idx, item in enumerate(line.split(','))}
        vpn_list.append(vpn_info)
    return vpn_list


class AutoVPNConnect:
    url_list_vpn: str = 'https://www.vpngate.net/api/iphone/'
    config_path: str
    country_code: str = None
    vpn_list: list = None
    current_index: int = None
    random: bool
    process = None
    sec_change_ip: int = None
    is_force_stopped: bool = False

    def update_list_file(self) -> list:
        file_dir = f"{ROOT_DIR}tmp/vpn-history"
        os.makedirs(file_dir, exist_ok=True)
        interval = datetime.datetime.now().hour % 10
        file_path = f"{file_dir}/{datetime.datetime.now().strftime('%Y-%m-%d_')}{interval}.json"
        if os.path.isfile(file_path):
            print(f'{bcolors.C_87}LOAD FILE with cache{bcolors.ENDC}')
            vpn_list = json.load(open(file_path))
        else:
            print(f'{bcolors.OKGREEN}UPLOAD FILE with {self.url_list_vpn}{bcolors.ENDC}')
            vpn_list = get_vpn_list(self.url_list_vpn)
            self.current_index = -1
        vpn_list.sort(key=lambda item: item['speed'], reverse=True)
        save_json(vpn_list, file_path)
        if self.country_code:
            filter(lambda item: item['country_short'] == self.country_code, vpn_list)
        self.vpn_list = vpn_list
        return vpn_list

    def save_config_file(self, vpn_config):
        self.config_path = f"{ROOT_DIR}tmp/autovpn_config.ovpn"
        open(self.config_path, 'wb').write(
            base64.b64decode(vpn_config['open_v_p_n__config_data__base64'])
        )

    def init_config(self):
        self.update_list_file()
        if self.vpn_list is None or not len(self.vpn_list):
            msg = 'Not init index.'
            print(f'{bcolors.FAIL}{msg}{bcolors.ENDC}')
            raise RuntimeError(msg)
        count = len(self.vpn_list)
        if self.random:
            self.current_index = random.randint(0, count - 1)
        else:
            next_index = self.current_index + 1
            self.current_index = 0 if count < next_index else next_index
        config = self.vpn_list[self.current_index]
        logging.info('INIT CONFIG:' + str(config))
        self.save_config_file(config)
        speed_mb = int(config["speed"]) / (1024 * 1024)
        print(f'{bcolors.C_GREEN}INIT CONFIG:{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Host name: {config["host_name"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Country: {config["country_long"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Country CODE: {config["country_short"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- ID: {config["i_p"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Ping: {config["ping"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Speed: {round(speed_mb, 2)} Mb{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Total users: {config["total_users"]}{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}- Operator: {config["operator"]}{bcolors.ENDC}')

    def __init__(self, country_code, _random=False, sec_change_ip=None, _attempts=6, _time_track_ip=180):
        self.random = _random
        self.attempts = _attempts
        self.time_track_ip = _time_track_ip
        self.current_index = -1
        if sec_change_ip:
            self.sec_change_ip = sec_change_ip
        if country_code:
            self.country_code = country_code.upper()
        self.current_index = -1

    def __del__(self):
        if self.process:
            self.process.kill()
            print(f'{bcolors.FAIL}Stop class and process {self.process.pid}{bcolors.ENDC}')
            os.kill(os.getpid(), signal.SIGKILL)

    def run(self, count: int = 1):
        self.is_force_stopped = False
        origin_ip = track_my_ip()
        msg = f'{bcolors.C_GREEN}CURRENT IP: {origin_ip}{bcolors.ENDC}'
        print(msg)
        logging.info(msg)
        self.init_config()
        self.process = subprocess.Popen(['openvpn', '--auth-nocache', '--config', self.config_path])
        print(f'{bcolors.C_YELLOW}Run....{bcolors.ENDC}')
        print(f'{bcolors.OKBLUE}Process PID {self.process.pid} start loop.{bcolors.ENDC}')
        logging.info('RUN VPN')
        loop = 0
        loop_track_ip = 0
        while self.process.poll() != 0:
            count = 1
            time.sleep(1)
            loop_track_ip = loop_track_ip + 1
            if not loop_track_ip % self.time_track_ip and origin_ip == track_my_ip():
                msg = f'{bcolors.FAIL}IP:{origin_ip}.RESET CONNECT{bcolors.ENDC}'
                print(msg)
                logging.info(msg.upper())
                break
            if not self.sec_change_ip:
                continue
            loop = loop + 1
            if loop > self.sec_change_ip:
                count = 1
                msg = f'{bcolors.BOLD}New connect once in {self.sec_change_ip}{bcolors.ENDC}'
                print(msg)
                logging.info(msg.upper())
                break
        self.process.kill()
        logging.info('STOP VPN')
        print(f'{bcolors.FAIL}Process PID {self.process.pid} killed{bcolors.ENDC}')
        self.process = None
        if not self.is_force_stopped and count == self.attempts:
            msg = f'{bcolors.WARNING}VPN server stopped attempt {count}.{bcolors.ENDC}'
            print(msg)
            logging.info(msg.upper())
            raise RuntimeError(msg)
        count = count + 1
        self.run(count)


def init_arguments() -> list:
    parser = argparse.ArgumentParser(description='Run FREE VPN SERVER. chech your IP: https://suip.biz/?act=myip')
    parser.add_argument(
        '--att',
        nargs='?',
        type=str,
        dest='attempts',
        help='The number of attempts to obtain errors before shutdown(default 5)',
        default=5
    )
    parser.add_argument(
        '--tp_ip',
        nargs='?',
        type=str,
        dest='time_ping_ip',
        help='The time of the poll has changed my ip(default 120)',
        default=120
    )
    parser.add_argument(
        '--c',
        nargs='?',
        type=str,
        dest='country',
        help='Country code if exist in list',
        default=None
    )
    parser.add_argument(
        '--r',
        nargs='?',
        type=bool,
        dest='is_random',
        help='Random VPN service(default True)',
        default=True
    )
    args = parser.parse_args()
    return [args.attempts, args.time_ping_ip, args.country, args.is_random]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        attempts, time_ping_ip, country, random = init_arguments()
        logging.info('START VPN')
        connect = AutoVPNConnect(country, random, time_ping_ip, attempts)


        def ctrl_z(e, r):
            print(f'{bcolors.C_BLUE}FORCED STOP:{bcolors.ENDC}')
            print(f'{bcolors.C_GREEN}GOOD LOCK!!!{bcolors.ENDC}')
            connect.__del__()


        def ctrl_c(e, r):
            connect.is_force_stopped = True
            print(f'{bcolors.C_GREEN}FORCED NEXT VPN SERVER{bcolors.ENDC}')


        signal.signal(signal.SIGTSTP, ctrl_z)  # ctrl + z
        signal.signal(signal.SIGINT, ctrl_c)  # ctrl + c
        connect.run()
    except RuntimeError as error:
        print(f"{bcolors.WARNING}RUNTIME ERROR:{bcolors.ENDC}", error)

    logging.info('END VPN')
    print(f"{bcolors.UNDERLINE}STOP VPN{bcolors.ENDC}")
