FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV DHCP_INTERFACE=eth0
ENV LEASES_FILE=/var/lib/kea/dhcp4.leases
ENV INVENTORY_DIR=/ansible_inventory
ENV TFTP_DIR=/var/lib/tftpboot

# Install required packages
RUN apt update && apt install -y \
    kea-dhcp4-server \
    ufw \
    tftpd-hpa \
    nginx \
    python3 \
    python3-pip \
    ansible \
    net-tools \
    iproute2 \
    libcap2-bin \
    jq \
    tcpdump \
    systemd \
    python3-flask \
    curl \
    python3-netifaces \
    python3-psutil \
    && rm -rf /var/lib/apt/lists/*

# Ensure necessary directories exist
RUN mkdir -p /var/lib/kea && touch /var/lib/kea/dhcp4.leases && chmod 644 /var/lib/kea/dhcp4.leases
RUN mkdir -p ${TFTP_DIR} && chmod 777 ${TFTP_DIR}
RUN mkdir -p /etc/kea  # Ensure /etc/kea exists

# Copy necessary configuration files and scripts
COPY generate_inventory.py /usr/local/bin/generate_inventory.py
COPY startup.sh /usr/local/bin/startup.sh
COPY dynamic_dhcp.py /usr/local/bin/dynamic_dhcp.py

# Copy Arista, Cisco, and Juniper configuration files
COPY startup-configs/arista_eos.conf ${TFTP_DIR}/arista_eos.conf
COPY startup-configs/ios_config.txt ${TFTP_DIR}/ios_config.txt
COPY startup-configs/juniper_config.conf ${TFTP_DIR}/juniper_config.conf

# Copy Kea DHCP configuration
COPY kea-dhcp4.conf /etc/kea/kea-dhcp4.conf  

# Set execute permissions
RUN chmod +x /usr/local/bin/generate_inventory.py /usr/local/bin/startup.sh
RUN chmod 644 ${TFTP_DIR}/arista_eos.conf ${TFTP_DIR}/ios_config.txt ${TFTP_DIR}/juniper_config.conf /etc/kea/kea-dhcp4.conf  

# Ensure TFTP to run in foreground mode
RUN echo 'TFTP_DIRECTORY="/var/lib/tftpboot"' > /etc/default/tftpd-hpa && \
    echo 'TFTP_OPTIONS="--secure --create --foreground"' >> /etc/default/tftpd-hpa

# Expose required ports
EXPOSE 67/udp 69/udp 80/tcp 5000/tcp

# Create a volume for Ansible inventory
VOLUME ["/ansible_inventory"]

# ---------------------
# API additions start
# ---------------------

# Copy API server file (api.py) into the container
COPY api.py /usr/local/bin/api.py

RUN ufw allow 5000/tcp || true

# ---------------------
# API additions end
# ---------------------

# ✅ Run startup script and keep container running
CMD ["/bin/bash", "/usr/local/bin/startup.sh"]