#!/bin/bash
set -x  # Enable debug mode

echo "🚀 Assigning static IP to eth0..."
ip addr add 192.168.100.50/24 dev eth0 || echo "❌ Failed to set IP on eth0"
ip link set eth0 up || echo "❌ Failed to bring up eth0"

echo "🚀 Stopping any running DHCP instance..."
pkill dhcpd || echo "No running DHCP found."

echo "🚀 Starting DHCP Server..."
dhcpd -cf /etc/dhcp/dhcpd.conf -lf /var/lib/dhcp/dhcpd.leases eth0 || { echo "❌ Failed to start DHCP"; exit 1; }

echo "🚀 Starting TFTP Server..."
service tftpd-hpa restart || { echo "❌ Failed to start TFTP"; exit 1; }

echo "🚀 Starting Nginx..."
service nginx restart || { echo "❌ Failed to start Nginx"; exit 1; }

echo "🚀 Ensuring syslog is running..."
service syslog start || echo "❌ Failed to start syslog"

echo "🚀 Extracting assigned IPs and detecting vendors..."
python3 /usr/local/bin/vendor_detect.py > /var/log/vendor_detection.log || { echo "❌ Vendor detection failed"; exit 1; }

echo "🚀 Generating Ansible inventory..."
mkdir -p /ansible_inventory
python3 /usr/local/bin/generate_inventory.py > /ansible_inventory/hosts || { echo "❌ Ansible inventory generation failed"; exit 1; }

echo "✅ ZTP Server is running. Watching logs..."
tail -f /var/log/messages /var/log/dhcp.log /var/log/vendor_detection.log
