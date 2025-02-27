import psutil
import netifaces
import ipaddress

def get_active_network_interface():
    """
    Get the active network interface based on network traffic.
    """
    stats = psutil.net_if_stats()
    active_interface = None
    max_bytes = 0

    for interface, stat in stats.items():
        if stat.isup and not interface.startswith(('lo', 'docker', 'veth')):
            # Get the number of bytes sent and received
            io_counters = psutil.net_io_counters(pernic=True)[interface]
            total_bytes = io_counters.bytes_sent + io_counters.bytes_recv
            if total_bytes > max_bytes:
                max_bytes = total_bytes
                active_interface = interface

    return active_interface

def get_interface_ip_and_subnet(interface):
    """
    Get the IP address and subnet mask of the given interface.
    """
    addresses = netifaces.ifaddresses(interface)
    if netifaces.AF_INET in addresses:
        ip_info = addresses[netifaces.AF_INET][0]
        ip = ip_info['addr']
        netmask = ip_info['netmask']
        return ip, netmask
    return None, None

def calculate_subnet_and_ips(ip, netmask):
    """
    Calculate the subnet and available IPs for DHCP.
    """
    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
    available_ips = list(network.hosts())
    return network, available_ips

def main():
    active_interface = get_active_network_interface()
    if active_interface:
        ip, netmask = get_interface_ip_and_subnet(active_interface)
        if ip and netmask:
            network, available_ips = calculate_subnet_and_ips(ip, netmask)
            subnet = str(network.network_address)
            netmask_str = str(network.netmask)
            range_start = str(available_ips[0])
            range_end = str(available_ips[-1])
            router_ip = ip  # Assuming the router IP is the same as the host IP

            print(f"export ZTP_IP={router_ip}")
            print(f"export SUBNET={subnet}")
            print(f"export NETMASK={netmask_str}")
            print(f"export RANGE_START={range_start}")
            print(f"export RANGE_END={range_end}")
            print(f"export ROUTER_IP={router_ip}")
        else:
            print("Could not retrieve IP address and subnet mask.")
    else:
        print("No active network interface found.")

if __name__ == "__main__":
    main()
