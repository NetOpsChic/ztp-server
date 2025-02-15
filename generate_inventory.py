import os

LEASES_FILE = "/var/lib/dhcp/dhcpd.leases"
INVENTORY_FILE = "/ansible_inventory/hosts"

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
    with open(INVENTORY_FILE, "w") as inv_file:
        inv_file.write("[routers]\n")
        for ip in assigned_ips:
            inv_file.write(f"{ip} ansible_user=admin ansible_password=admin\n")
    print("✅ Ansible inventory generated!")
