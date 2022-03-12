import base64
import datetime
import json
import os
import random
import re
import signal
import subprocess
import time

import psutil
import requests


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
    ATTEMPTS: int = 5
    config_path: str
    country_code: str = None
    vpn_list: list = None
    current_index: int = None
    is_random: bool
    process = None

    def update_list_file(self) -> list:
        file_path = f"var/vpn-history/{datetime.datetime.now().strftime('%Y-%m-%d_%H')}.json"
        # file_path = f"var/vpn-history/{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')}.json"
        if os.path.isfile(file_path):
            print(f'{bcolors.OKBLUE}LOAD FILE with cache{bcolors.ENDC}')
            vpn_list = json.load(open(file_path))
        else:
            print(f'{bcolors.OKGREEN}UPLOAD FILE with {self.url_list_vpn}{bcolors.ENDC}')
            vpn_list = get_vpn_list(self.url_list_vpn)
        vpn_list.sort(key=lambda item: item['speed'], reverse=True)
        save_json(vpn_list, file_path)
        if self.country_code:
            filter(lambda item: item['country_short'] == self.country_code, vpn_list)
        self.vpn_list = vpn_list
        return vpn_list

    def save_config_file(self, vpn_config):
        self.config_path = f"var/configs/{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}"
        open(self.config_path, 'wb').write(
            base64.b64decode(vpn_config['open_v_p_n__config_data__base64'])
        )

    def init_config(self):
        if self.current_index is None or self.vpn_list is None or not len(self.vpn_list):
            msg = 'Not init index.'
            print(f'{bcolors.FAIL}{msg}{bcolors.ENDC}')
            raise RuntimeError(msg)
        count = len(self.vpn_list)
        if self.is_random:
            self.current_index = random.randint(0, count - 1)
        config = self.vpn_list[self.current_index]
        self.save_config_file(config)
        next_index = self.current_index + 1
        self.current_index = 0 if count < next_index else next_index
        speed_mb = int(config["speed"]) / (1024 * 1024)
        print(f'{bcolors.C_YELLOW}INIT CONFIG:{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Host name: {config["host_name"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Country: {config["country_long"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Country CODE: {config["country_short"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- ID: {config["i_p"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Ping: {config["ping"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Speed: {speed_mb} Mb{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Total users: {config["total_users"]}{bcolors.ENDC}')
        print(f'{bcolors.C_YELLOW}- Operator: {config["operator"]}{bcolors.ENDC}')

    def __init__(self, country_code: str = None, is_random: bool = False, target_host: str = None):
        self.target_host = target_host
        self.is_random = is_random
        self.current_index = 0
        if country_code:
            self.country_code = country_code.upper()
        self.update_list_file()

    def __del__(self):
        if self.process:
            self.process.kill()
            print(f'{bcolors.FAIL}Stop class and process {self.process.pid}{bcolors.ENDC}')
            os.kill(os.getpid(), signal.SIGKILL)

    def run(self, count: int = 1):
        self.init_config()
        self.process = subprocess.Popen(['sudo', 'openvpn', '--auth-nocache', '--config', self.config_path])
        with self.process:
            print(f'{bcolors.WARNING}Run....{bcolors.ENDC}')
        print(f'{bcolors.OKBLUE}Process PID {self.process.pid} start loop.{bcolors.ENDC}')
        while self.process.poll() != 0:
            time.sleep(1)
            # TODO: ping target_host and reset
        self.process.kill()
        print(f'{bcolors.FAIL}Process PID {self.process.pid} killed{bcolors.ENDC}')
        self.process = None
        if count == self.ATTEMPTS:
            msg = f'VPN server stopped attempt {count}.'
            print(msg)
            print(f'{bcolors.WARNING}{msg}{bcolors.ENDC}')
            raise RuntimeError(msg)
        count = count + 1
        self.run(count)


def kill_all_old_process(process_name: str):
    process = [(int(p), c) for p, c in
               [x.rstrip('\n').split(' ', 1) for x in os.popen(f'ps h -eo pid:1,command | grep {process_name}')]]
    # print(process)
    processes = filter(lambda p: 'grep' not in p[1].lower(), process)
    for proc in processes:
        if os.getpid() != proc[0]:
            print(f'{bcolors.FAIL}   - KILL PID:{proc[0]},CMD:{proc[1]} {bcolors.ENDC}')
            os.popen(f'sudo kill -9 {proc[0]}')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    def ctrl_z(e, r):
        print(f'{bcolors.C_BLUE}FORCED STOP:{bcolors.ENDC}')
        kill_all_old_process('main.py')
        print(f'{bcolors.C_GREEN}- All main.py{bcolors.ENDC}')
        kill_all_old_process('openvpn')
        print(f'{bcolors.C_GREEN}- All openvpn{bcolors.ENDC}')
        exit()


    signal.signal(signal.SIGTSTP, ctrl_z)  # ctrl + z
    try:
        connect = AutoVPNConnect('ru', True)
        connect.run()
    except RuntimeError as error:
        print(f"{bcolors.WARNING}RUNTIMEERROR:{bcolors.ENDC}", error)

    print(f"{bcolors.UNDERLINE}STOP VPN{bcolors.ENDC}")
