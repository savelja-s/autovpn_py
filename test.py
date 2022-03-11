import re


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


def run():
    r = file_to_array('var/www.vpngate.net.txt')
    te = 1


if __name__ == '__main__':
    run()
