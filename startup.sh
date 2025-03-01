#!/bin/bash

# ✅ Environment Variables for manual input

ZTP_IP=${ZTP_IP:-192.168.100.2}    
SUBNET=${SUBNET:-192.168.100.0}        
NETMASK=${NETMASK:-255.255.255.0}      
RANGE_START=${RANGE_START:-192.168.100.3}  
RANGE_END=${RANGE_END:-192.168.100.254}    
ROUTER_IP=${ROUTER_IP:-192.168.100.2}
DNS_SERVERS=${DNS_SERVERS:-"8.8.8.8, 8.8.4.4"}

# ✅ Configure Kea DHCP Server
echo "🚀 Configuring Kea DHCP Server..."
sed -i "s|{{SUBNET}}|$SUBNET|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{NETMASK}}|$NETMASK|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{RANGE_START}}|$RANGE_START|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{RANGE_END}}|$RANGE_END|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{ZTP_IP}}|$ZTP_IP|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{ROUTER_IP}}|$ROUTER_IP|g" /etc/kea/kea-dhcp4.conf
sed -i "s|{{DNS_SERVERS}}|$DNS_SERVERS|g" /etc/kea/kea-dhcp4.conf

# ✅ Assign static IP to eth0
echo "🚀 Assigning static IP to eth0 - ZTP IP: $ZTP_IP/24"
ip addr add "$ZTP_IP/24" dev eth0 || echo "⚠️ Failed to assign static IP"
ip link set eth0 up

# ✅ Enable firewall rule for port 5000 (UFW)
if command -v ufw >/dev/null 2>&1; then
  echo "🚀 Allowing inbound TCP on port 5000 via UFW..."
  ufw enable || echo "⚠️ Failed to enable UFW"
  ufw allow 5000/tcp || echo "⚠️ Failed to add UFW rule for 5000/tcp"
  # You might also want ufw enable, but be cautious about enabling UFW blindly if it isn't enabled
else
  echo "⚠️ UFW not found, skipping firewall rule for port 5000."
fi

# ✅ Ensure required directories for Kea logs and PID files exist
echo "🚀 Ensuring Kea runtime directories exist..."
mkdir -p /var/run/kea /run/kea /var/log/kea /var/lib/kea
chmod 755 /var/run/kea /run/kea /var/log/kea /var/lib/kea

# ✅ Ensure Kea lease file exists before starting
LEASE_FILE="/var/lib/kea/kea-leases4.csv"
echo "🚀 Ensuring Kea lease file exists: $LEASE_FILE"
touch "$LEASE_FILE"
chmod 644 "$LEASE_FILE"

echo "🚀 Starting Kea DHCP Server in the background..."
kea-dhcp4 -c /etc/kea/kea-dhcp4.conf > /var/log/kea/kea-dhcp4.log 2>&1 &
sleep 2  # Give Kea some time to initialize

# ✅ Ensure TFTP directory exists
echo "🚀 Ensuring TFTP directory exists..."
mkdir -p /var/lib/tftpboot
chmod 777 /var/lib/tftpboot

# ✅ Start TFTP Server
echo "🚀 Starting TFTP Server..."
service tftpd-hpa stop
/usr/sbin/in.tftpd -l -s /var/lib/tftpboot --verbose --foreground &

# ✅ Start Nginx
echo "🚀 Starting Nginx..."
service nginx restart || { echo "❌ Failed to start Nginx"; exit 1; }

# ✅ Wait up to 5 minutes (300 seconds) for active DHCP leases
echo "⏳ Waiting for active DHCP leases (max 5 minutes)..."
MAX_WAIT_TIME=300  # Maximum wait time in seconds
CHECK_INTERVAL=10  # Interval to check for leases
TOTAL_WAIT=0

while [ $TOTAL_WAIT -lt $MAX_WAIT_TIME ]; do
    echo "🔍 Checking for active DHCP leases... (Waited $TOTAL_WAIT seconds)"
    cat /var/lib/kea/kea-leases4.csv

    if grep -qE "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" /var/lib/kea/kea-leases4.csv; then
        echo "✅ Active DHCP lease found! Proceeding with vendor detection."

        # ✅ Run vendor detection script for ZTP assignments
        python3 /usr/local/bin/vendor_detect.py

        break
    fi

    echo "⏳ No active DHCP leases yet, waiting $CHECK_INTERVAL seconds..."
    sleep $CHECK_INTERVAL
    TOTAL_WAIT=$((TOTAL_WAIT + CHECK_INTERVAL))
done

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

# ✅ Start API Server
echo "🚀 Starting API server..."
python3 /usr/local/bin/api.py &

echo "✅ ZTP Server is running!"

# Keep the container alive by tailing logs
tail -f /dev/null
