from flask import Flask, jsonify
import os
import csv

app = Flask(__name__)

# Define file paths (adjust if necessary)
LEASES_FILE = "/var/lib/kea/kea-leases4.csv"
INVENTORY_FILE = "/ansible_inventory/hosts"

def parse_inventory():
    """Parses the Ansible inventory file and returns a dictionary grouped by vendor."""
    if not os.path.exists(INVENTORY_FILE):
        return {}
    inventory = {}
    current_group = None
    with open(INVENTORY_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Lines like [cisco] indicate a vendor group
            if line.startswith("[") and line.endswith("]"):
                current_group = line[1:-1]
                inventory[current_group] = []
            else:
                if current_group:
                    inventory[current_group].append(line)
    return inventory

def parse_leases():
    """Reads the Kea DHCP leases CSV file and returns a list of lease entries."""
    if not os.path.exists(LEASES_FILE):
        return []
    leases = []
    with open(LEASES_FILE, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            leases.append(row)
    return leases

@app.route("/inventory", methods=["GET"])
def get_inventory():
    """API endpoint to get the current Ansible inventory as JSON."""
    inventory = parse_inventory()
    return jsonify(inventory)

@app.route("/leases", methods=["GET"])
def get_leases():
    """API endpoint to get the current DHCP leases as JSON."""
    leases = parse_leases()
    return jsonify(leases)

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Listen on all interfaces on port 5000
    app.run(host="0.0.0.0", port=5000)
