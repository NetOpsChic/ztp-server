#!/usr/bin/env python3
import csv
import os

# Path to the local IEEE OUI file (downloaded manually)
OUI_FILE = "/usr/local/etc/oui.txt"

def load_oui_mapping(oui_file):
    """
    Load the OUI mapping from a local file.
    Expected lines contain a prefix and "(hex)" or "(base 16)" such as:
      FC-59-C0   (hex)            Arista Networks
    This function converts the prefix to a colon-separated string.
    """
    mapping = {}
    if not os.path.exists(oui_file):
        print(f"Warning: OUI file not found: {oui_file}")
        return mapping

    with open(oui_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "(hex)" in line or "(base 16)" in line:
                parts = line.split("(hex)")
                if len(parts) < 2:
                    parts = line.split("(base 16)")
                if len(parts) == 2:
                    prefix = parts[0].strip().replace('-', ':').lower()
                    vendor = parts[1].strip()
                    mapping[prefix] = vendor
    return mapping

# Build the OUI mapping from the offline file.
OUI_MAPPING = load_oui_mapping(OUI_FILE)

# CUSTOM_VENDOR_MAP: Add known OUIs that the IEEE file may not contain.
CUSTOM_VENDOR_MAP = {
    "0c:34:d1": "Arista"
}

def get_vendor_from_mac(mac):
    """
    Extract the OUI (first three octets) from the MAC address and return
    the vendor name. Custom mapping is checked first.
    """
    parts = mac.split(':')
    if len(parts) < 3:
        return "unknown"
    oui = ":".join(parts[:3]).lower()
    if oui in CUSTOM_VENDOR_MAP:
        return CUSTOM_VENDOR_MAP[oui]
    return OUI_MAPPING.get(oui, "unknown")

def detect_vendor(client_id, hwaddr=""):
    """
    Detect the vendor based on the DHCP Option 60 (client_id).
    If client_id is empty or invalid and a hardware address is provided,
    it falls back to using the hardware address for vendor lookup.
    
    - If client_id is a standard MAC address (6 groups), an OUI lookup is performed.
    - If it’s a longer (hex-encoded) string, an attempt is made to decode it;
      if that fails, the first 6 groups are used as a fallback.
    """
    client_id = client_id.strip()
    # Fallback to hwaddr if client_id is empty or does not contain a colon.
    if not client_id or ":" not in client_id:
        if hwaddr:
            print("DEBUG: client_id empty or invalid, falling back to hwaddr.")
            return get_vendor_from_mac(hwaddr.strip())
        return "unknown"

    parts = client_id.split(":")
    if len(parts) == 6:
        mac = ":".join(parts).lower()
        vendor = get_vendor_from_mac(mac)
        print(f"DEBUG: Detected vendor from MAC {mac}: {vendor}")
        return vendor
    elif len(parts) > 6:
        # Attempt to decode hex-encoded ASCII.
        hex_str = "".join(parts)
        try:
            decoded = bytes.fromhex(hex_str).decode("utf-8", errors="ignore")
            lower_decoded = decoded.lower()
            if lower_decoded.startswith("arista"):
                return "Arista"
            elif lower_decoded.startswith("cisco"):
                return "Cisco"
            elif lower_decoded.startswith("juniper"):
                return "Juniper"
        except Exception as e:
            print(f"DEBUG: Exception decoding hex: {e}")
        # Fallback: use the first 6 groups.
        mac = ":".join(parts[:6]).lower()
        vendor = get_vendor_from_mac(mac)
        print(f"DEBUG: Fallback detected vendor from MAC {mac}: {vendor}")
        return vendor
    return "unknown"

if __name__ == "__main__":
    # For testing: parse a Kea lease CSV and print vendor detection.
    KEA_LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
    if not os.path.exists(KEA_LEASES_FILE):
        print(f"Error: Kea DHCP leases file not found: {KEA_LEASES_FILE}")
    else:
        with open(KEA_LEASES_FILE, "r") as leases_file:
            reader = csv.DictReader(leases_file)
            if not reader.fieldnames:
                print("Error: Lease file is empty or has an invalid format.")
            else:
                for row in reader:
                    ip_address = row.get("address", "").strip()
                    client_id = row.get("client_id", "").strip()
                    hwaddr = row.get("hwaddr", "").strip()  # Fallback hardware MAC
                    if not ip_address:
                        continue
                    vendor_name = detect_vendor(client_id, hwaddr)
                    print(f"Detected Vendor: {vendor_name} (IP: {ip_address}) - Client ID: {client_id}")
