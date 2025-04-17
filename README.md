# ZTP (Zero Touch Provisioning) Server

## Overview
This ZTP server automates the provisioning of network devices using **DHCP, TFTP, and Ansible**. It dynamically assigns IP addresses, generates an **Ansible inventory** for automated configuration deploymen and exposing inventory at API endpoint /inventory at http://ZTP_IP:5000/inventory

## Features
- **DHCP Server**: Assigns IP addresses dynamically.
- **TFTP Server**: Provides initial configuration files.
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
   git clone https://github.com/netopschic/ztp-server.git
   cd ztp-server
   ```

2. **Build the Docker image**:
   ```sh
   docker build -t ztp-server .
   ```

## Configuration
### Environment Variables
You can override the default settings using environment variables:

In order to find your values simple run
```sh
   python3 dynamic_dhcp.py
   ```

The values generated can be replace by the values in startup.sh 
| Variable | Description | Default Value |
|----------|-------------|---------------|
| `ZTP_IP` | IP address of the ZTP server | `192.168.100.50` |
| `ROUTER_IP` | Default gateway | `192.168.100.1` |
| `SUBNET` | Network subnet | `192.168.100.0` |
| `NETMASK` | Subnet mask | `255.255.255.0` |
| `RANGE_START` | DHCP start range | `192.168.100.100` |
| `RANGE_END` | DHCP end range | `192.168.100.200` |

## How It Works
1. **DHCP Server** assigns an IP to the router.
3. **TFTP Server** provides the correct startup configuration file.
4. **Ansible Inventory** is automatically updated with the assigned IPs.
5. **Ansible Playbooks** can now configure the devices.
6. **API server** for fetching the inventory at http://ZTP_IP:5000/inventory

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
  - Verify DHCP lease using: `cat /var/lib/dhcp/kea-dhcp.leases`
  - Restart the router interface.
- **Ansible inventory is empty**:
  - Run the inventory script manually: `python3 /usr/local/bin/generate_inventory.py`

## Contributing
Feel free to submit issues or contribute via pull requests.

## License
MIT License. See `LICENSE` for details.
