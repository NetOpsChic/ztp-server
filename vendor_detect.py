#!/usr/bin/env python3

import csv
import subprocess
import os

KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"  # Correct lease file location
LOG_FILE = "/var/log/ztp.log"

VENDOR_LOOKUP = {
    "00:1C:73": "arista",   # Arista MAC prefix
    "00:1A:1E": "cisco",    # Cisco MAC prefix
    "00:1B:21": "juniper"   # Juniper MAC prefix
}

def detect_vendor(mac_address):
    """Detect vendor based on MAC address OUI."""
    for prefix, name in VENDOR_LOOKUP.items():
        if mac_address.lower().startswith(prefix.lower()):
            return name
    return "unknown"

def log_ztp_assignment(mac_address, ip_address, vendor, ztp_config):
    """Log ZTP assignment to a file."""
    log_entry = f"MAC: {mac_address}, IP: {ip_address}, Vendor: {vendor}, Config: {ztp_config}\n"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)

def get_latest_lease():
    """Retrieve the latest lease from Kea's lease file."""
    if not os.path.exists(KEA_LEASES_FILE):
        print(f"❌ Error: Lease file not found: {KEA_LEASES_FILE}")
        return None, None

    try:
        with open(KEA_LEASES_FILE, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header if needed
            leases = list(reader)

        if not leases:
            print("❌ Error: No valid DHCP leases found.")
            return None, None

        last_lease = leases[-1]  # Get last lease entry
        mac_address = last_lease[0]
        ip_address = last_lease[1]
        return mac_address, ip_address

    except Exception as e:
        print(f"❌ Error reading lease file: {str(e)}")
        return None, None

def main():
    mac_address, ip_address = get_latest_lease()
    
    if not mac_address or not ip_address:
        print("❌ No valid DHCP lease found.")
        return

    vendor = detect_vendor(mac_address)
    ztp_config = "default-ztp.cfg"

    if vendor == "arista":
        ztp_config = "arista_eos.conf"
    elif vendor == "cisco":
        ztp_config = "ztp-config"

    log_ztp_assignment(mac_address, ip_address, vendor, ztp_config)

    # Output assignment confirmation
    subprocess.run(["echo", f"ZTP Config assigned: {ztp_config} for {vendor} ({ip_address})"])

if __name__ == "__main__":
    main()
