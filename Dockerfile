# Use Ubuntu as the base image
FROM ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DHCP_INTERFACE=eth0
ENV LEASES_FILE=/var/lib/dhcp/dhcpd.leases
ENV INVENTORY_DIR=/ansible_inventory

# Install necessary packages
RUN apt update && apt install -y \
    isc-dhcp-server \
    tftpd-hpa \
    nginx \
    python3 \
    python3-pip \
    ansible \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Ensure DHCP lease file exists
RUN mkdir -p /var/lib/dhcp && touch /var/lib/dhcp/dhcpd.leases && chmod 644 /var/lib/dhcp/dhcpd.leases

# Copy required scripts and configurations
COPY dhcpd.conf /etc/dhcp/dhcpd.conf
COPY vendor_detect.py /usr/local/bin/vendor_detect.py
COPY generate_inventory.py /usr/local/bin/generate_inventory.py
COPY startup.sh /usr/local/bin/startup.sh

# Set execute permissions
RUN chmod +x /usr/local/bin/vendor_detect.py /usr/local/bin/generate_inventory.py /usr/local/bin/startup.sh

# Ensure DHCP binds to eth0 only
RUN echo 'INTERFACESv4="eth0"' > /etc/default/isc-dhcp-server && \
    echo 'INTERFACESv6=""' >> /etc/default/isc-dhcp-server

# Expose required ports
EXPOSE 67/udp 69/udp 80/tcp

# Add NET_ADMIN Capability to Ensure DHCP Can Bind to Ports
RUN apt install -y libcap2-bin && setcap CAP_NET_ADMIN+ep /usr/sbin/dhcpd

# ✅ **Create volume for Ansible inventory**
VOLUME ["/ansible_inventory"]

# ✅ **Run startup script on container boot**
CMD ["/bin/bash", "/usr/local/bin/startup.sh"]
