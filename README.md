# ZTP (Zero Touch Provisioning) Server

## Overview
This ZTP server automates the provisioning of network devices using **DHCP, TFTP, and Ansible**. It dynamically assigns IP addresses, detects vendor information, and generates an **Ansible inventory** for automated configuration deployment.

## Features
- **DHCP Server**: Assigns IP addresses dynamically.
- **TFTP Server**: Provides initial configuration files.
- **Vendor Detection**: Identifies devices based on MAC addresses.
- **Ansible Integration**: Automatically generates inventory for configuration management.
- **Automatic Sync**: Exports the generated inventory to the local system.

## Prerequisites
Ensure the following are installed on your system before running the ZTP server:
- **Docker** (for containerized deployment)
- **Ansible** (for executing playbooks on provisioned devices)
- **GNS3** (if running in a network simulation environment)

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/your-repo/ztp-server.git
   cd ztp-server
   ```

2. **Build the Docker image**:
   ```sh
   docker build -t ztp-server .
   ```

3. **Run the ZTP server**:
   ```sh
   docker run --rm --name ztp-server \
     --cap-add=NET_ADMIN \
     -v $(pwd)/ansible_inventory:/mnt/ansible_inventory \
     -p 67:67/udp -p 69:69/udp -p 80:80 \
     ztp-server
   ```

## Configuration
### Environment Variables
You can override the default settings using environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `ZTP_IP` | IP address of the ZTP server | `192.168.100.50` |
| `ROUTER_IP` | Default gateway | `192.168.100.1` |
| `SUBNET` | Network subnet | `192.168.100.0` |
| `NETMASK` | Subnet mask | `255.255.255.0` |
| `RANGE_START` | DHCP start range | `192.168.100.100` |
| `RANGE_END` | DHCP end range | `192.168.100.200` |

Example:
```sh
docker run --rm --name ztp-server \
  --cap-add=NET_ADMIN \
  -v $(pwd)/ansible_inventory:/mnt/ansible_inventory \
  -e ZTP_IP=192.168.100.60 \
  -e RANGE_START=192.168.100.150 \
  -e RANGE_END=192.168.100.250 \
  ztp-server
```

## How It Works
1. **DHCP Server** assigns an IP to the router.
2. **Vendor Detection** determines the device manufacturer.
3. **TFTP Server** provides the correct startup configuration file.
4. **Ansible Inventory** is automatically updated with the assigned IPs.
5. **Ansible Playbooks** can now configure the devices.

## Checking Ansible Inventory
Once the ZTP process is completed, check the generated inventory:
```sh
cat ansible_inventory/hosts
```

If the inventory exists, you can run an Ansible playbook to configure the devices:
```sh
ansible-playbook -i ansible_inventory/hosts your-playbook.yml
```

## Troubleshooting
- **ZTP server fails to start**:
  - Check logs using: `docker logs ztp-server`
  - Ensure Docker has `NET_ADMIN` capability.
- **No IP is assigned to the router**:
  - Verify DHCP lease using: `cat /var/lib/dhcp/dhcpd.leases`
  - Restart the router interface.
- **Ansible inventory is empty**:
  - Run the inventory script manually: `python3 /usr/local/bin/generate_inventory.py`

## Contributing
Feel free to submit issues or contribute via pull requests.

## License
MIT License. See `LICENSE` for details.
