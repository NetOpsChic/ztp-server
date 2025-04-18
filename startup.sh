#!/bin/bash

# ✅ Environment Variables
ZTP_IP=${ZTP_IP:-192.168.100.3}
SUBNET=${SUBNET:-192.168.100.0}
NETMASK=${NETMASK:-255.255.255.0}
RANGE_START=${RANGE_START:-192.168.100.5}
RANGE_END=${RANGE_END:-192.168.100.254}
ROUTER_IP=${ROUTER_IP:-192.168.100.4}
DNS_SERVERS=${DNS_SERVERS:-"8.8.8.8, 8.8.4.4"}
BROADCAST_IP=${BROADCAST_IP:-192.168.100.255}

# ✅ Update Kea DHCP Configuration
echo "🚀 Configuring Kea DHCP Server..."
sed -i "s|\${SUBNET}|$SUBNET|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${NETMASK}|$NETMASK|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${RANGE_START}|$RANGE_START|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${RANGE_END}|$RANGE_END|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${ZTP_IP}|$ZTP_IP|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${ROUTER_IP}|$ROUTER_IP|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${DNS_SERVERS}|$DNS_SERVERS|g" /etc/kea/kea-dhcp4.conf
sed -i "s|\${BROADCAST_IP}|$BROADCAST_IP|g" /etc/kea/kea-dhcp4.conf

# ✅ Assign static IP to eth0
echo "🚀 Assigning static IP to eth0 - ZTP IP: $ZTP_IP/24"
ip addr add "$ZTP_IP/24" dev eth0 || echo "⚠️ Failed to assign static IP"
ip link set eth0 up

# ✅ Prepare Kea runtime directories
echo "🚀 Preparing Kea runtime directories..."
mkdir -p /var/run/kea /run/kea /var/log/kea /var/lib/kea
chmod 755 /var/run/kea /run/kea /var/log/kea /var/lib/kea

# ✅ Ensure lease file exists
LEASE_FILE="/var/lib/kea/kea-leases4.csv"
touch "$LEASE_FILE"
chmod 644 "$LEASE_FILE"

# ✅ Start Kea DHCP Server
echo "🚀 Starting Kea DHCP Server..."
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf > /var/log/kea/kea-dhcp4.log 2>&1 &
sleep 2

# ✅ Prepare TFTP directory
echo "🚀 Preparing TFTP directory..."
mkdir -p /var/lib/tftpboot
chmod 777 /var/lib/tftpboot

# ✅ Start TFTP Server
echo "🚀 Starting TFTP Server..."
service tftpd-hpa stop
/usr/sbin/in.tftpd -l -s /var/lib/tftpboot --verbose --foreground &

# ✅ Start Nginx (optional static file server)
echo "🚀 Starting Nginx..."
service nginx restart || { echo "❌ Failed to start Nginx"; exit 1; }

# ✅ Wait for DHCP lease stabilization (max 5 min)
echo "⏳ Waiting for active DHCP leases (max 5 minutes)..."
MAX_WAIT_TIME=300  # seconds
CHECK_INTERVAL=10
TOTAL_WAIT=0

while [ $TOTAL_WAIT -lt $MAX_WAIT_TIME ]; do
    echo "🔍 Checking for active DHCP leases... (Waited $TOTAL_WAIT seconds)"
    cat "$LEASE_FILE"

    if grep -qE "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" "$LEASE_FILE"; then
        echo "✅ Active DHCP lease found!"
        break
    fi

    echo "⏳ No lease yet. Waiting $CHECK_INTERVAL seconds..."
    sleep $CHECK_INTERVAL
    TOTAL_WAIT=$((TOTAL_WAIT + CHECK_INTERVAL))
done

# ✅ Generate Ansible inventory (with retries)
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

# ✅ Start API server
echo "🚀 Starting API server..."
python3 /usr/local/bin/api.py &

echo "✅ ZTP Server is running and stable!"

# ⏳ Keep container alive
tail -f /dev/null
