#!/usr/bin/env python3
import os
import csv
import time
import vendor_detect  # Import vendor detection logic

# Paths and settings
KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
INVENTORY_FILE = "/ansible_inventory/hosts"
ROUTER_IP = "192.168.100.2"  # Exclude this IP

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
    For each hardware address, select the lease with the highest timestamp,
    which is assumed to be the most recent (active) lease.
    """
    inventory = {}
    leases = {}  # Dictionary keyed by hwaddr

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
            # Assume the CSV columns as:
            # 0: IP address, 1: hwaddr, 2: client_id, 3: lease_duration, 4: lease_time, ...
            headers = ["address", "hwaddr", "client_id", "lease_duration", "lease_time"]
            data_rows = [first_row] + list(csv_reader)
        else:
            headers = first_row
            data_rows = list(csv_reader)

        # Determine indices (try multiple header names if necessary)
        if "address" in headers:
            ip_idx = headers.index("address")
        elif "ame" in headers:
            ip_idx = headers.index("ame")
        else:
            ip_idx = 0

        if "hwaddr" in headers:
            hwaddr_idx = headers.index("hwaddr")
        else:
            hwaddr_idx = 1

        if "client_id" in headers:
            clientid_idx = headers.index("client_id")
        elif "user_context" in headers:
            clientid_idx = headers.index("user_context")
        else:
            clientid_idx = 2

        # For the timestamp, try to use a header called "lease_time"
        if "lease_time" in headers:
            lease_time_idx = headers.index("lease_time")
        else:
            lease_time_idx = 4  # Assume column index 4 if no header is present

        for row in data_rows:
            if len(row) < max(ip_idx, hwaddr_idx, clientid_idx, lease_time_idx) + 1:
                continue

            current_ip = row[ip_idx].strip()
            client_id = row[clientid_idx].strip().lower().replace("-", ":")
            hwaddr = row[hwaddr_idx].strip().lower().replace("-", ":")
            try:
                timestamp = int(row[lease_time_idx].strip())
            except ValueError:
                timestamp = 0

            # Skip if any field is missing or if it's the router's IP.
            if not current_ip or not client_id or not hwaddr or current_ip == ROUTER_IP:
                continue

            # If the same hwaddr exists, keep the lease with the highest timestamp.
            if hwaddr not in leases or timestamp > leases[hwaddr]["timestamp"]:
                leases[hwaddr] = {"ip": current_ip, "client_id": client_id, "timestamp": timestamp}
                print(f"🔄 Updated lease for {hwaddr.upper()}: {current_ip} (Timestamp: {timestamp})")

    # Build the inventory from the selected leases.
    for hwaddr, lease_info in leases.items():
        latest_ip = lease_info["ip"]
        client_id = lease_info["client_id"]
        vendor_name = vendor_detect.detect_vendor(client_id)
        if vendor_name not in inventory:
            inventory[vendor_name] = []
        inventory[vendor_name].append(f"{latest_ip} ansible_user=admin ansible_password=admin")
        print(f"🔍 Final Inventory Entry: HWADDR {hwaddr.upper()} (ClientID: {client_id.upper()}) → {latest_ip} (Timestamp: {lease_info['timestamp']})")

    return inventory

def generate_inventory():
    """Generate the Ansible inventory from Kea leases."""
    # Optional: delay to allow the DHCP lease file to settle after device reboot.
    time.sleep(120)
    inventory = parse_kea_leases()
    if inventory:
        # Ensure the inventory directory exists.
        inv_dir = os.path.dirname(INVENTORY_FILE)
        if not os.path.exists(inv_dir):
            os.makedirs(inv_dir)
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
