#!/usr/bin/env python3
import os
import csv
import vendor_detect  # Import vendor detection logic

# Paths and settings
KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
INVENTORY_FILE = "/ansible_inventory/hosts"
ROUTER_IP = "192.168.100.1"  # Exclude this IP

def is_ip(s):
    """Simple check if a string looks like an IPv4 address."""
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
    return True

def parse_kea_leases():
    """
    Parse the Kea DHCP lease CSV file and extract valid leases.
    This version supports headers "ame", "user_context", and "hwaddr"
    (or "address", "client_id", and "hwaddr"). It uses the hardware address
    to prevent duplicate entries.
    """
    inventory = {}
    seen_hwaddrs = set()  # Track hardware addresses to avoid duplicates

    if not os.path.exists(KEA_LEASES_FILE):
        print(f"❌ Error: Kea DHCP leases file not found: {KEA_LEASES_FILE}")
        return None

    if os.path.getsize(KEA_LEASES_FILE) == 0:
        print("❌ Error: Kea lease file is empty.")
        return None

    with open(KEA_LEASES_FILE, "r") as leases_file:
        csv_reader = csv.reader(leases_file)
        first_row = next(csv_reader, None)
        if not first_row:
            print("❌ Error: Kea lease file is empty.")
            return None

        # If the first field looks like an IP, assume no header.
        if is_ip(first_row[0]):
            headers = ["ame", "hwaddr", "user_context", "pool_id"]
            data_rows = [first_row] + list(csv_reader)
        else:
            headers = first_row
            data_rows = list(csv_reader)

        # Determine which header set to use.
        if "ame" in headers and "user_context" in headers and "hwaddr" in headers:
            ip_idx = headers.index("ame")
            clientid_idx = headers.index("user_context")
            hwaddr_idx = headers.index("hwaddr")
        elif "address" in headers and "client_id" in headers and "hwaddr" in headers:
            ip_idx = headers.index("address")
            clientid_idx = headers.index("client_id")
            hwaddr_idx = headers.index("hwaddr")
        else:
            print("❌ Error: Kea lease file format is invalid. Expected headers including 'hwaddr'.")
            return None

        for row in data_rows:
            if len(row) < max(ip_idx, clientid_idx, hwaddr_idx) + 1:
                continue

            current_ip = row[ip_idx].strip()
            client_id = row[clientid_idx].strip().lower().replace("-", ":")
            hwaddr = row[hwaddr_idx].strip().lower().replace("-", ":")

            if not current_ip or not client_id or not hwaddr or current_ip == ROUTER_IP:
                continue

            # Use hwaddr for duplicate check.
            if hwaddr in seen_hwaddrs:
                continue
            seen_hwaddrs.add(hwaddr)

            vendor_name = vendor_detect.detect_vendor(client_id)
            if vendor_name not in inventory:
                inventory[vendor_name] = []
            inventory[vendor_name].append(f"{current_ip} ansible_user=admin ansible_password=admin")
            print(f"🔍 Lease Found: HWADDR {hwaddr.upper()} (ClientID: {client_id.upper()}) → {current_ip}")

    return inventory

def generate_inventory():
    """Generate the Ansible inventory from Kea leases."""
    inventory = parse_kea_leases()
    if inventory:
        with open(INVENTORY_FILE, "w") as inv_file:
            for vendor_name, devices in inventory.items():
                inv_file.write(f"[{vendor_name}]\n")
                for entry in devices:
                    inv_file.write(f"{entry}\n")
                inv_file.write("\n")
        print("✅ Ansible inventory generated successfully!")
    else:
        print("❌ No valid DHCP leases found. Inventory not updated.")

if __name__ == "__main__":
    generate_inventory()
