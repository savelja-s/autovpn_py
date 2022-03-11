# autovpn3, coded by MiAl,
# you can leave a bug report on the page: https://miloserdov.org/?p=5858
# сообщить об ошибке на русском вы можете на странице: https://HackWare.ru/?p=15429

# you can change these parameters:
import os
import re

import requests

country = ''  # empty for any or JP, KR, US, TH, etc.
useSavedVPNlist = 0  # set to 1 if you don't want to download VPN list every time you restart this script, otherwise set to 0
useFirstServer = 0  # set the value to 0 to choose a random VPN server, otherwise set to 1 (maybe the first one has higher score)
vpnList = 'var/vpns.lst'
proxy = 0  # replace with 1 if you want to connect to VPN server through a proxy
proxyIP = ''
proxyPort = 8080
proxyType = 'socks'  # socks or http
# don't change this:
counter = 0
VPNproxyString = ''
cURLproxyString = ''


def download_file(url: str, file_name: str):
    r = requests.get(url, allow_redirects=True)
    open(file_name, 'wb').write(r.content)


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
    return vpn_list


if proxy == 1:
    print('We will use a proxy')
    if not proxyIP:
        print("To use a proxy, you must specify the proxy's IP address and port (hardcoded in the source code).")
        exit()
    else:
        if proxyType == 'socks':
            VPNproxyString = ' --socks-proxy $proxyIP $proxyPort '
            cURLproxyString = ' --proxy socks5h://{proxyIP}:{proxyPort} '
        elif proxyType == 'http':
            VPNproxyString = f' --http-proxy {proxyIP} {proxyPort} '
            cURLproxyString = f' --proxy http://{proxyIP}:{proxyPort} '
        else:
            print('Unsupported proxy type.')
            exit()
if useSavedVPNlist == 0:
    print('Getting the VPN list')
    download_file('https://www.vpngate.net/api/iphone/', vpnList)
elif not os.path.exists(vpnList) or os.stat(vpnList).st_size == 0:
    print('Getting the VPN list')
    download_file('https://www.vpngate.net/api/iphone/', vpnList)
else:
    print('Using existing VPN list')

array = file_to_array(vpnList)


class CreateVPNConfig:
    size: int

    def __init__(self, vpn_config: list):
        if not len(vpn_config):
            msg = 'No VPN servers found from the selected country.'
            print(msg)
            raise RuntimeError(msg)
        self.size = len(vpn_config)
        if useFirstServer == 1:
            index = 0
        #     if [ $useFirstServer -eq 1 ]; then
        #         index=0
        #         echo ${array[$index]} | awk -F "," '{ print $15 }' | base64 -d > /tmp/openvpn3
        #     else
        #         index=$(($RANDOM % $size))
        #         echo ${array[$index]} | awk -F "," '{ print $15 }' | base64 -d > /tmp/openvpn3
        #     fi
        #     echo 'Choosing a VPN server:'
        #     echo "Found VPN servers: $((size+1))"
        #     echo "Selected: $index"
        #     echo "Country: `echo ${array[$index]} | awk -F "," '{ print $6 }'`"


def run_vpn():
    pass
    # while true
    #     do
    #         CreateVPNConfig
    #         echo 'Trying to start OpenVPN client'
    #         sudo openvpn --config /tmp/openvpn3 $VPNproxyString
    #         read -p "Try another VPN server? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit
    #     done


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_vpn()
