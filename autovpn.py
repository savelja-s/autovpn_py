#!/usr/bin/env python3

import datetime
import os
import signal
import subprocess
import time
import argparse
import logging

from vpn_config import track_my_ip, bcolors, VPNConfig

# ROOT_DIR: str = os.path.dirname(__file__) + '/'
ROOT_DIR: str = '/'
TMP_DIR: str = ROOT_DIR + 'tmp/'
LOGFILE_PATH = f'{ROOT_DIR}tmp/autovpn_current.log'
SEC_TO_CONNECT = 8

logging.basicConfig(filename=f'{ROOT_DIR}var/log/autovpn_py.log',
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)


class AutoVPNConnect(object):
    url_list_vpn: str = 'https://www.vpngate.net/api/iphone/'
    random: bool
    country_code: str = None
    vpn_list: list = None
    current_index: int = None
    process = None
    sec_change_ip: int = None
    is_force_stopped: bool = False
    run_at = None
    is_started_VPN = False

    def ctrl_z(self, e, r):
        print(f'{bcolors.C_BLUE}FORCED STOP:{bcolors.ENDC}')
        print(f'{bcolors.C_GREEN}GOOD LOCK!!!{bcolors.ENDC}')
        self.__del__()

    def ctrl_c(self, e, r):
        self.is_force_stopped = True
        print(f'{bcolors.C_GREEN}FORCED NEXT VPN SERVER{bcolors.ENDC}')

    def __init__(self, country_code, _random=False, sec_change_ip=None, _time_track_ip=180):
        self.origin_ip = track_my_ip()
        self.random = _random
        self.time_track_ip = _time_track_ip
        self.current_index = -1
        if sec_change_ip:
            self.sec_change_ip = sec_change_ip
        if country_code:
            self.country_code = country_code.upper()
        self.current_index = -1
        signal.signal(signal.SIGTSTP, self.ctrl_z)  # ctrl + z
        signal.signal(signal.SIGINT, self.ctrl_c)  # ctrl + c

    def __del__(self):
        if self.process:
            self.process.kill()
            print(f'{bcolors.FAIL}Stop class and process {self.process.pid}{bcolors.ENDC}')
            os.kill(os.getpid(), signal.SIGKILL)

    def read_stdout(self):
        # print('READ_STDOUT')
        with open(LOGFILE_PATH, 'r') as log_file:
            content = log_file.read()
            if not self.is_started_VPN and content.count('Initialization Sequence Completed'):
                print('Initialization Sequence Completed')
                self.is_started_VPN = True
            count_restart = content.count('Restart pause,')
            if count_restart:
                print(f'Restart № {count_restart}')
        # print('END_STDOUT')

    def _handler_vpn_loop(self) -> bool:
        while self.process.poll() != 0:
            time.sleep(1)
            self.read_stdout()
            if not self.is_started_VPN:
                print('VPN Status', self.is_started_VPN)
            sec_worked = round((datetime.datetime.now() - self.run_at).total_seconds())
            # print('LOOP TIME', sec_worked)
            interval_track = sec_worked % self.time_track_ip
            if not self.is_started_VPN and sec_worked >= SEC_TO_CONNECT:
                msg = f'{bcolors.FAIL}next server if not connect on {SEC_TO_CONNECT} seconds{bcolors.ENDC}'.upper()
                print(msg)
                logging.info(msg)
                return False
            elif interval_track > self.time_track_ip and self.origin_ip == track_my_ip():
                msg = f'{bcolors.FAIL}IP:{self.origin_ip}.RESET CONNECT{bcolors.ENDC}'
                print(msg)
                logging.info(msg.upper())
                return False
            elif self.sec_change_ip and sec_worked > self.sec_change_ip:
                msg = f'{bcolors.BOLD}New connect once in {self.sec_change_ip}{bcolors.ENDC}'
                print(msg)
                logging.info(msg.upper())
                return True
        return False

    def init_process(self, config_path: str):
        self.is_started_VPN = False
        self.is_force_stopped = False
        self.run_at = datetime.datetime.now()
        with open(LOGFILE_PATH, 'w+') as log_file:
            process = subprocess.Popen([
                'openvpn',
                '--connect-retry-max',
                '1',
                '--verb',
                '4',
                '--auth-nocache',
                '--config',
                config_path
            ], stdout=log_file, encoding='utf-8', bufsize=1)
        msg = f'{bcolors.C_YELLOW}Run... {bcolors.ENDC}{bcolors.OKBLUE}process PID {process.pid} start loop.{bcolors.ENDC}'
        print(msg)
        self.process = process

    def print_current_ip(self):
        msg = f'{bcolors.C_GREEN}CURRENT IP: {self.origin_ip}{bcolors.ENDC}'
        print(msg)
        logging.info(msg)

    def run(self, vpn_config: VPNConfig = None):
        if not vpn_config:
            vpn_config = VPNConfig(TMP_DIR, self.url_list_vpn, self.country_code, self.random)
        else:
            self.print_current_ip()
        self.init_process(vpn_config.config_path)
        logging.info('RUN VPN')
        self._handler_vpn_loop()
        self.process.kill()
        logging.info('STOP VPN')
        print(f'{bcolors.FAIL}Process PID {self.process.pid} killed{bcolors.ENDC}')
        self.process = None
        self.print_current_ip()
        vpn_config.init_config()
        self.run(vpn_config)


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
        attempts, time_ping_ip, country, _random = init_arguments()
        logging.info('START VPN')
        AutoVPNConnect(country, _random, time_ping_ip, attempts).run()
    except RuntimeError as error:
        print(f"{bcolors.WARNING}RUNTIME ERROR:{bcolors.ENDC}", error)

    logging.info('END VPN')
    print(f"{bcolors.UNDERLINE}STOP VPN{bcolors.ENDC}")
