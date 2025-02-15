import os

LEASES_FILE = "/var/lib/dhcp/dhcpd.leases"
VENDOR_MAP = {
    "00:1A:1E": "Cisco",
    "00:1B:21": "Juniper",
    "00:1C:73": "Arista"
}

def detect_vendor(mac_address):
    prefix = mac_address[:8].upper()
    return VENDOR_MAP.get(prefix, "Unknown")

def extract_assigned_ips():
    assigned_ips = []
    with open(LEASES_FILE, "r") as file:
        for line in file:
            if "lease" in line:
                ip = line.split()[1]
                assigned_ips.append(ip)
    return assigned_ips

if __name__ == "__main__":
    assigned_ips = extract_assigned_ips()
    for ip in assigned_ips:
        mac_address = "00:1A:1E:XX:XX:XX"  # Simulated for now
        vendor = detect_vendor(mac_address)
        startup_config = f"{vendor.lower()}_config.txt"
        print(f"IP {ip} is assigned to {vendor}, using {startup_config}")
