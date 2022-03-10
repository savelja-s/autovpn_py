# autovpn3, coded by MiAl,
# you can leave a bug report on the page: https://miloserdov.org/?p=5858
# сообщить об ошибке на русском вы можете на странице: https://HackWare.ru/?p=15429

# you can change these parameters:
country = ''  # empty for any or JP, KR, US, TH, etc.
useSavedVPNlist = 0  # set to 1 if you don't want to download VPN list every time you restart this script, otherwise set to 0
useFirstServer = 0  # set the value to 0 to choose a random VPN server, otherwise set to 1 (maybe the first one has higher score)
vpnList = '/tmp/vpns.tmp'
proxy = 0  # replace with 1 if you want to connect to VPN server through a proxy
proxyIP = ''
proxyPort = 8080
proxyType = 'socks'  # socks or http

def run_vpn():
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
