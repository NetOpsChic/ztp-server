#!/bin/bash

# Environment Variables
ZTP_IP=${ZTP_IP:-192.168.100.50}    
ROUTER_IP=${ROUTER_IP:-192.168.100.1}  
SUBNET=${SUBNET:-192.168.100.0}        
NETMASK=${NETMASK:-255.255.255.0}      
RANGE_START=${RANGE_START:-192.168.100.100}  
RANGE_END=${RANGE_END:-192.168.100.200}      

echo "🚀 Configuring DHCP Server..."
sed -i "s|{{SUBNET}}|$SUBNET|g" /etc/dhcp/dhcpd.conf
sed -i "s|{{NETMASK}}|$NETMASK|g" /etc/dhcp/dhcpd.conf
sed -i "s|{{RANGE_START}}|$RANGE_START|g" /etc/dhcp/dhcpd.conf
sed -i "s|{{RANGE_END}}|$RANGE_END|g" /etc/dhcp/dhcpd.conf
sed -i "s|{{ROUTER_IP}}|$ROUTER_IP|g" /etc/dhcp/dhcpd.conf
sed -i "s|{{ZTP_IP}}|$ZTP_IP|g" /etc/dhcp/dhcpd.conf

echo "🚀 Assigning static IP to eth0 - ZTP IP: $ZTP_IP/24"
ip addr add "$ZTP_IP/24" dev eth0
ip link set eth0 up

echo "🚀 Stopping any running DHCP instance..."
pkill dhcpd || echo "No running DHCP found."

echo "🚀 Starting DHCP Server..."
dhcpd -cf /etc/dhcp/dhcpd.conf -lf /var/lib/dhcp/dhcpd.leases eth0 || { echo "❌ Failed to start DHCP"; exit 1; }

echo "🚀 Starting TFTP Server..."
service tftpd-hpa restart || { echo "❌ Failed to start TFTP"; exit 1; }

echo "🚀 Starting Nginx..."
service nginx restart || { echo "❌ Failed to start Nginx"; exit 1; }

echo "🚀 Ensuring Ansible inventory directory exists..."
mkdir -p /ansible_inventory
mkdir -p /mnt/ansible_inventory  # Ensure sync path exists

# ✅ Ensure valid DHCP leases before proceeding
echo "⏳ Waiting for active DHCP leases..."
for attempt in $(seq 1 10); do
    echo "🔍 Checking for active DHCP leases (Attempt $attempt/10)..."
    cat /var/lib/dhcp/dhcpd.leases
    if grep -q "binding state active" /var/lib/dhcp/dhcpd.leases; then
        echo "✅ Active DHCP lease found! Proceeding with inventory generation."
        break
    fi
    echo "⏳ No active DHCP leases yet, retrying in 5 sec..."
    sleep 5
done

if ! grep -q "binding state active" /var/lib/dhcp/dhcpd.leases; then
    echo "❌ No valid DHCP leases found after retries. Skipping inventory generation."
    exit 1
fi

# ✅ Generate Ansible inventory with retries
for attempt in {1..3}; do
    echo "🚀 Generating Ansible inventory (Attempt $attempt/3)..."
    python3 /usr/local/bin/generate_inventory.py

    echo "🔍 Debug: Current Inventory File Contents"
    cat /ansible_inventory/hosts || echo "❌ Inventory file not found"

    if grep -qE "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" /ansible_inventory/hosts; then
        echo "✅ Ansible inventory successfully generated!"
        break
    fi

    echo "⏳ Inventory not valid yet. Retrying in 5 seconds..."
    sleep 5
done

if ! grep -qE "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" /ansible_inventory/hosts; then
    echo "❌ Ansible inventory generation failed after retries."
    exit 1
fi

# ✅ Copy inventory to /etc/ansible/hosts
echo "🚀 Copying Ansible inventory to /etc/ansible/hosts..."
mkdir -p /etc/ansible
cp /ansible_inventory/hosts /etc/ansible/hosts || echo "❌ Failed to copy inventory to /etc/ansible/hosts"

# ✅ Sync inventory to the local machine
echo "🚀 Syncing inventory to local machine..."
cp /ansible_inventory/hosts /mnt/ansible_inventory/hosts || echo "❌ Failed to sync inventory to local machine."

echo "✅ ZTP Server is running!"
tail -f /dev/null
