#!/usr/bin/env python3
import os
import csv
import time

# Paths and settings
KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
INVENTORY_FILE = "/ansible_inventory/hosts"
ROUTER_IP = "192.168.100.2"  # Exclude this IP from inventory

def is_ip(s):
    parts = s.split('.')
    return len(parts) == 4 and all(p.isdigit() for p in parts)

def parse_kea_leases():
    inventory = []
    leases = {}

    if not os.path.exists(KEA_LEASES_FILE) or os.path.getsize(KEA_LEASES_FILE) == 0:
        print(f"❌ Error: Kea lease file missing or empty: {KEA_LEASES_FILE}")
        return None

    with open(KEA_LEASES_FILE, "r") as f:
        reader = csv.reader(f)
        first_row = next(reader, None)
        if not first_row:
            print("❌ Error: Kea lease file is empty.")
            return None

        headers = first_row if not is_ip(first_row[0]) else ["address", "hwaddr", "client_id", "lease_duration", "lease_time"]
        data_rows = [first_row] + list(reader) if is_ip(first_row[0]) else list(reader)

        ip_idx = headers.index("address") if "address" in headers else 0
        hw_idx = headers.index("hwaddr") if "hwaddr" in headers else 1
        lease_time_idx = headers.index("lease_time") if "lease_time" in headers else 4

        for row in data_rows:
            if len(row) <= max(ip_idx, hw_idx, lease_time_idx):
                continue

            ip = row[ip_idx].strip()
            mac = row[hw_idx].strip().lower().replace("-", ":")
            try:
                ts = int(row[lease_time_idx].strip())
            except ValueError:
                ts = 0

            if not is_ip(ip) or ip == ROUTER_IP:
                continue

            if mac not in leases or ts > leases[mac]["timestamp"]:
                leases[mac] = {"ip": ip, "timestamp": ts}
                print(f"🔄 Updated lease for {mac.upper()}: {ip} (Timestamp: {ts})")

    for lease in leases.values():
        inventory.append(lease["ip"])
        print(f"🔍 Final inventory IP: {lease['ip']}")

    return inventory

def generate_inventory():
    time.sleep(120)  # Lease stabilization wait

    device_ips = parse_kea_leases()
    if not device_ips:
        print("❌ No valid DHCP leases found.")
        return

    os.makedirs(os.path.dirname(INVENTORY_FILE), exist_ok=True)

    with open(INVENTORY_FILE, "w") as f:
        f.write("[routers]\n")
        for ip in device_ips:
            f.write(f"{ip}\n")
    print(f"✅ Inventory written to {INVENTORY_FILE}")

if __name__ == "__main__":
    generate_inventory()
