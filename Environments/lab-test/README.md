# Lab-Test Environment

This directory contains the configuration and deployment scripts for the **lab-test** Kubernetes cluster.

## Quick Start

To deploy the lab-test cluster, simply run:

```bash
./script.sh
```

Or for non-interactive deployment:

```bash
./script.sh deploy
```

## Files

- **`vars.yml`** - Environment-specific variables and configuration
- **`main.yml`** - Cluster definition and deployment configuration  
- **`script.sh`** - Simple deployment script with interactive menu
- **`README.md`** - This documentation file

## Configuration

Edit `vars.yml` to customize:
- Network settings (IPs, VIPs, subnets)
- Node specifications (CPU, memory, disk)
- Service configurations
- Security settings
- Backup settings

## Usage

The deployment script supports both interactive and command-line modes:

### Interactive Mode
```bash
./script.sh
```

### Command Line Mode
```bash
./script.sh deploy     # Deploy new cluster
./script.sh upgrade    # Upgrade existing cluster
./script.sh validate   # Validate cluster
./script.sh cleanup    # Remove cluster
./script.sh inventory  # Generate inventory only
./script.sh status     # Show cluster status
```

## Requirements

- Ansible installed
- Python 3 installed
- SSH access to target hosts
- VMware vSphere access (if using VM provisioning)

## Cluster Details

- **Environment**: lab-test
- **Datacenter**: WTD
- **Network**: 192.168.56.0/24
- **Kubernetes Version**: Kubespray default (latest)
- **CNI**: Calico
- **Nodes**: 1 master, 2 workers, 2 HAProxy

## Support

For issues or questions, refer to the main project documentation or contact the infrastructure team.