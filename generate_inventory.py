import os
import time
import re

# File paths
LEASES_FILE = "/var/lib/dhcp/dhcpd.leases"
INVENTORY_FILE = "/ansible_inventory/hosts"

# Vendor mappings
VENDOR_MAP = {
    "00:1A:1E": "cisco",
    "00:1B:21": "juniper",
    "00:1C:73": "arista"
}

def detect_vendor(mac_address):
    """ Detect vendor based on MAC address OUI """
    prefix = mac_address[:8].upper()
    return VENDOR_MAP.get(prefix, "unknown")

def parse_leases():
    """ Parse the DHCP lease file and extract valid leases """
    inventory = {}
    found_leases = False

    if not os.path.exists(LEASES_FILE):
        print(f"❌ Error: DHCP leases file not found: {LEASES_FILE}")
        return None

    with open(LEASES_FILE, "r") as leases:
        current_ip = None
        current_mac = None
        current_hostname = None

        for line in leases:
            line = line.strip()

            if line.startswith("lease "):  
                current_ip = line.split()[1]  
            elif "hardware ethernet" in line:
                current_mac = line.split()[-1].strip(";").lower()
            elif "client-hostname" in line:
                current_hostname = line.split()[-1].strip('";')

            if current_ip and current_mac:  
                vendor = detect_vendor(current_mac)
                if vendor not in inventory:
                    inventory[vendor] = []
                inventory[vendor].append(f"{current_ip} ansible_user=admin ansible_password=admin")

                print(f"🔍 Lease Found: {current_mac.upper()} → {current_ip} (Hostname: {current_hostname})")
                found_leases = True

                current_ip, current_mac, current_hostname = None, None, None  

    return inventory if found_leases else None

def generate_inventory():
    """ Generate the Ansible inventory with retries """
    attempts = 5
    delay = 10  

    for attempt in range(1, attempts + 1):
        print(f"🚀 Attempting to generate inventory (Try {attempt}/{attempts})...")

        inventory = parse_leases()

        if inventory:
            with open(INVENTORY_FILE, "w") as inv_file:
                for vendor, devices in inventory.items():
                    inv_file.write(f"[{vendor}]\n")
                    for entry in devices:
                        inv_file.write(f"{entry}\n")
                    inv_file.write("\n")

            print("✅ Ansible inventory generated successfully!")
            return  

        print(f"⏳ No valid DHCP leases found, retrying in {delay} sec... (Attempt {attempt}/{attempts})")
        time.sleep(delay)

    print("❌ No valid DHCP leases found after retries. Inventory not updated.")

if __name__ == "__main__":
    generate_inventory()
