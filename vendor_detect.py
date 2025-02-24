#!/usr/bin/env python3
import csv
import os
import subprocess

KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
LOG_FILE = "/var/log/ztp.log"

VENDOR_LOOKUP = {
    "00:1C:73": "arista",   # Arista MAC prefix
    "00:1A:1E": "cisco",    # Cisco MAC prefix
    "00:1B:21": "juniper"   # Juniper MAC prefix
}

CONFIG_MAP = {
    "arista": "startup-configs/arista_eos.conf",
    "cisco": "startup-configs/ios_config.txt",
    "juniper": "startup-configs/juniper_config.conf",
    "unknown": "default-ztp.cfg"
}

def detect_vendor(mac_address):
    """
    Detect vendor based on MAC address OUI.
    """
    for prefix, name in VENDOR_LOOKUP.items():
        if mac_address.lower().startswith(prefix.lower()):
            return name
    return "unknown"

def parse_kea_csv():
    """Parse Kea CSV lease file."""
    inventory = {}

    if not os.path.exists(KEA_LEASES_FILE):
        print(f"❌ Error: Kea DHCP leases file not found: {KEA_LEASES_FILE}")
        return None

    with open(KEA_LEASES_FILE, "r") as leases_file:
        reader = csv.reader(leases_file)
        next(reader, None)  # Skip the header if it exists

        for row in reader:
            try:
                ip_address = row[0].strip()
                mac_address = row[1].strip()

                if not ip_address or not mac_address:
                    continue  # Ignore empty rows

                vendor = detect_vendor(mac_address)
                ztp_config = CONFIG_MAP.get(vendor, "default-ztp.cfg")  # Assign appropriate config

                if vendor not in inventory:
                    inventory[vendor] = []

                inventory[vendor].append(f"{ip_address} ansible_user=admin ansible_password=admin")
                print(f"🔍 Lease Found: {mac_address.upper()} → {ip_address}, Config: {ztp_config}")

            except IndexError:
                print(f"⚠️ Skipping invalid row: {row}")

    return inventory

def generate_inventory():
    """Generate Ansible inventory."""
    inventory = parse_kea_csv()
    if inventory:
        with open("/ansible_inventory/hosts", "w") as inv_file:
            for vendor, devices in inventory.items():
                inv_file.write(f"[{vendor}]\n")
                for entry in devices:
                    inv_file.write(f"{entry}\n")
                inv_file.write("\n")

        print("✅ Ansible inventory generated successfully!")
    else:
        print("❌ No valid DHCP leases found. Inventory not updated.")

if __name__ == "__main__":
    generate_inventory()
