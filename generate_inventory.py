#!/usr/bin/env python3

import os
import csv

# ✅ Correct Kea lease file path (CSV, not JSON)
KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
INVENTORY_FILE = "/ansible_inventory/hosts"

# ✅ Vendor MAC prefixes
VENDOR_MAP = {
    "00:1A:1E": "cisco",
    "00:1B:21": "juniper",
    "00:1C:73": "arista"
}

ROUTER_IP = "192.168.100.1"  # ✅ Exclude this IP

def detect_vendor(mac_address):
    """Detect vendor based on MAC address OUI."""
    prefix = mac_address[:8].upper()  # ✅ Extract OUI
    return VENDOR_MAP.get(prefix, "unknown")

def parse_kea_leases():
    """Parse Kea DHCP lease CSV file and extract valid leases."""
    inventory = {}
    mac_ip_map = {}  # ✅ Track assigned IPs per MAC

    if not os.path.exists(KEA_LEASES_FILE):
        print(f"❌ Error: Kea DHCP leases file not found: {KEA_LEASES_FILE}")
        return None

    with open(KEA_LEASES_FILE, "r") as leases_file:
        csv_reader = csv.reader(leases_file)
        headers = next(csv_reader, None)  # ✅ Read header row
        
        if not headers or "address" not in headers or "hwaddr" not in headers:
            print("❌ Error: Kea lease file format is invalid.")
            return None

        # ✅ Get column indexes dynamically
        address_idx = headers.index("address")
        hwaddr_idx = headers.index("hwaddr")

        for row in csv_reader:
            if len(row) < max(address_idx, hwaddr_idx) + 1:
                continue

            current_ip = row[address_idx].strip()
            current_mac = row[hwaddr_idx].strip().lower().replace("-", ":")  # ✅ Normalize MAC address

            if not current_ip or not current_mac or current_ip == ROUTER_IP:
                continue  # ✅ Skip invalid or router IPs

            if current_mac in mac_ip_map:  # ✅ Prevent duplicate assignments
                continue

            mac_ip_map[current_mac] = current_ip
            vendor = detect_vendor(current_mac)

            if vendor not in inventory:
                inventory[vendor] = []

            inventory[vendor].append(f"{current_ip} ansible_user=admin ansible_password=admin")
            print(f"🔍 Lease Found: {current_mac.upper()} → {current_ip}")

    return inventory

def generate_inventory():
    """Generate the Ansible inventory from Kea leases."""
    inventory = parse_kea_leases()

    if inventory:
        with open(INVENTORY_FILE, "w") as inv_file:
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
