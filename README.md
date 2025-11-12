# 🚀 Kubernetes Cluster Automation with Kubespray

A production-ready Kubernetes deployment automation framework built on **Kubespray v2.29.0** with integrated HAProxy load balancing, automated backups, and complete lifecycle management.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [How to Run](#-how-to-run)
- [Configuration](#-configuration)
- [Available Commands](#-available-commands)
- [Deployment Phases](#-deployment-phases)
- [Access Points](#-access-points)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- **🏗️ Complete Kubernetes Deployment** - Automated cluster deployment using Kubespray
- **⚖️ Integrated Load Balancing** - HAProxy with Keepalived for high availability
- **🔍 Automatic VM Discovery** - Detects actual VM IPs via Vagrant
- **📋 Unified Inventory Generation** - Single script creates both Kubespray and HAProxy inventories
- **🎯 Multi-Environment Support** - Lab, Dev, Prod environments
- **💾 Automated Backups** - etcd and Kubernetes namespace backups
- **🔧 Maintenance Tasks** - Automated etcd defragmentation
- **🔐 OIDC Authentication** - Integrated with ADFS
- **📊 Monitoring Ready** - Metrics Server and Dashboard included

---

## 🔧 Prerequisites

### Required Software

```bash
# Install VirtualBox (for local VM deployment)
sudo apt update
sudo apt install -y virtualbox virtualbox-ext-pack

# Install Vagrant
sudo apt install -y vagrant

# Install Ansible
sudo apt install -y ansible

# Install Python 3 and dependencies
sudo apt install -y python3 python3-pip
pip3 install pyyaml

# Install sshpass for password authentication fallback
sudo apt install -y sshpass
```

### System Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: Minimum 50GB free
- **CPU**: 4+ cores recommended
- **OS**: Linux (Ubuntu/Debian) or macOS

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd k8s-multi-cluster-automation-feature-kubespray-automation
```

### 2. Start Virtual Machines

```bash
# Start all VMs (haproxy1, haproxy2, master1, worker1, worker2)
vagrant up
```

This will create:
- **2 HAProxy nodes** (haproxy1, haproxy2)
- **1 Master node** (master1)
- **2 Worker nodes** (worker1, worker2)

### 3. Deploy the Cluster

```bash
# Navigate to your environment directory
cd Environments/lab-test

# Run the deployment script
./script.sh deploy
```

That's it! The script will:
1. Generate inventories
2. Deploy Kubernetes cluster
3. Deploy HAProxy load balancers
4. Fix worker node configurations
5. Setup backups and maintenance
6. Validate the deployment

---

## 📁 Project Structure

```
k8s-multi-cluster-automation-feature-kubespray-automation/
├── Environments/                    # Environment configurations
│   └── lab-test/                   # Lab-test environment
│       ├── script.sh               # 🎯 Main deployment script
│       ├── vars.yml                # Environment-specific variables
│       ├── main.yml                # Additional configurations
│       └── README.md               # Environment documentation
├── scripts/
│   └── generate-all-inventories.py  # 🔧 Unified inventory generator
├── Ansible/
│   ├── inventory/                  # Generated inventory files
│   │   └── haproxy_inventory.ini
│   ├── playbooks/                  # Essential playbooks
│   │   ├── prepare_kernel_modules.yml   # Kernel module preparation
│   │   ├── prepare_system.yml           # System preparation
│   │   ├── deploy_haproxy_keepalived.yml # HAProxy deployment
│   │   ├── fix_worker_kubelet.yml       # Worker node fixes
│   │   ├── fix_cgroup_conf_kubelet.yml  # Kubernetes node cgroup fixes
│   │   ├── setup_backup.yml             # Backup setup
│   │   ├── setup_maintenance.yml        # Maintenance setup
│   │   └── validate_cluster.yml         # Cluster validation
│   └── templates/                  # Jinja2 templates
│       ├── backup-etcd.sh.j2
│       ├── backup-k8s-namespaces.sh.j2
│       └── defrag-etcd.sh.j2
├── Kubespray/                      # 📦 Kubespray v2.29.0
│   ├── cluster.yml                 # Main Kubespray playbook
│   └── inventory/                 # Generated Kubespray inventories
│       └── lab-test/
├── Vagrantfile                    # 🖥️ Local VM definitions
└── README.md                      # This file
```

---

## 🎯 How to Run

### Option 1: Interactive Menu

```bash
cd Environments/lab-test
./script.sh
```

You'll see an interactive menu:
```
🚀 Lab-Test Kubernetes Deployment Options:
  1) 🏗️  Deploy complete cluster (inventory + Kubespray + HAProxy)
  2) ⚖️  Deploy HAProxy only (requires existing cluster)
  3) 📋 Generate inventories only
  4) ✅ Validate cluster
  5) 📊 Show status
  6) 🚪 Exit
```

### Option 2: Command Line

```bash
cd Environments/lab-test

# Deploy complete cluster
./script.sh deploy

# Deploy HAProxy only
./script.sh haproxy

# Generate inventories only
./script.sh inventory

# Validate cluster
./script.sh validate

# Show cluster status
./script.sh status
```

---

## ⚙️ Configuration

### Environment Configuration

Edit `Environments/lab-test/vars.yml` to customize your cluster:

```yaml
# Cluster name (should match folder name)
cluster_name: lab-test

# Network configuration
network:
  prefix: "192.168.56"
  api_vip: "192.168.56.150"
  ingress_vip: "192.168.56.149"
  virtual_ip: "192.168.56.148"

# Node configuration
nodes:
  masters:
    - hostname: master1
      ip: "192.168.56.153"
  workers:
    - hostname: worker1
      ip: "192.168.56.154"
    - hostname: worker2
      ip: "192.168.56.155"
  haproxy:
    - hostname: haproxy1
      ip: "192.168.56.151"
      keepalived_state: MASTER
      keepalived_priority: 200
    - hostname: haproxy2
      ip: "192.168.56.152"
      keepalived_state: BACKUP
      keepalived_priority: 100

# OIDC configuration
oidc:
  enabled: true
  issuer_url: https://sts.medimpact.com/adfs
  client_id: 916d15d5-65f1-481e-9b1a-819c17b8414b

# Backup configuration
backup:
  enabled: true
  etcd_backup_schedule: "0 4 * * *"
  namespace_backup_schedule: "0 5 * * *"
```

### VM Configuration

Edit `Vagrantfile` to change VM resources:

```ruby
config.vm.provider "virtualbox" do |vb|
  vb.memory = "2048"    # RAM per VM
  vb.cpus = 2           # CPU cores per VM
end
```

---

## 📋 Available Commands

### Deployment Commands

| Command | Description |
|---------|-------------|
| `./script.sh deploy` | Complete cluster deployment (all phases) |
| `./script.sh haproxy` | Deploy HAProxy only (requires existing cluster) |
| `./script.sh inventory` | Generate inventories only |
| `./script.sh validate` | Validate cluster deployment |
| `./script.sh status` | Show cluster status |

### Manual Playbook Execution

```bash
# System preparation
ansible-playbook -i Kubespray/inventory/lab-test/inventory.ini \
  -e "@Environments/lab-test/vars.yml" \
  --become Ansible/playbooks/prepare_kernel_modules.yml

# HAProxy deployment
ansible-playbook -i Ansible/inventory/haproxy_inventory.ini \
  -e "@Environments/lab-test/vars.yml" \
  --become Ansible/playbooks/deploy_haproxy_keepalived.yml
```

---

## 🔄 Deployment Phases

When you run `./script.sh deploy`, it executes these phases:

### **Phase 1: System Preparation**
- Load kernel modules (`br_netfilter`, `bridge`)
- System compatibility checks
- Swap and firewall configuration

### **Phase 2: Kubernetes Cluster Deployment**
- Deploy Kubernetes via Kubespray
- Install CoreDNS, Metrics Server, Dashboard
- Configure NGINX Ingress Controller
- Setup Calico CNI networking

### **Phase 3: HAProxy Load Balancer**
- Deploy HAProxy on dedicated nodes
- Configure Keepalived for VIP failover
- Setup load balancing for API and Ingress

### **Phase 4: Worker Node Fix**
- Fix kubelet configuration on worker nodes
- Ensure correct API server endpoint

### **Phase 5: Kubernetes Node Fix**
- Fix kubelet configuration on master and worker nodes
- Ensure correct cgroup configurations applied

### **Phase 6: Backup Setup** (if enabled)
- Deploy etcd backup scripts
- Deploy Kubernetes namespace backup scripts
- Configure cron jobs

### **Phase 7: Maintenance Setup** (if enabled)
- Deploy etcd defragmentation scripts
- Configure maintenance cron jobs

### **Phase 8: Validation**
- Verify cluster health
- Check node status
- Validate services

---

## 🌐 Access Points

After successful deployment, access your cluster:

| Service | URL | Description |
|---------|-----|-------------|
| **Kubernetes API** | `https://192.168.56.150:6443` | Cluster management endpoint |
| **HAProxy Stats** | `http://192.168.56.150:8404/stats` | Load balancer dashboard |
| **HTTP Applications** | `http://192.168.56.150` | Web applications via Ingress |
| **HTTPS Applications** | `https://192.168.56.150` | Secure applications via Ingress |
| **Kubernetes Dashboard** | Access via `kubectl proxy` | Web UI for cluster management |

### Accessing the Cluster

```bash
# Get kubeconfig from master node
vagrant ssh master1
sudo cat /etc/kubernetes/admin.conf > ~/.kube/config

# Or copy to your local machine
vagrant ssh master1 -c "sudo cat /etc/kubernetes/admin.conf" > kubeconfig.yaml
export KUBECONFIG=./kubeconfig.yaml

# Verify access
kubectl get nodes
kubectl get pods --all-namespaces
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. VMs Not Starting

```bash
# Destroy and recreate VMs
vagrant destroy -f
vagrant up
```

#### 2. Inventory Generation Fails

```bash
# Check Python dependencies
pip3 install pyyaml

# Verify vars.yml syntax
python3 -c "import yaml; yaml.safe_load(open('Environments/lab-test/vars.yml'))"
```

#### 3. Deployment Fails at Phase 2 (Kubespray)

```bash
# Check cluster status
./script.sh status

# View Kubespray logs
tail -f /tmp/kubespray.log

# Retry deployment
./script.sh deploy
```

#### 4. Worker Nodes Not Ready

```bash
# Run Phase 4 manually
ansible-playbook -i Kubespray/inventory/lab-test/inventory.ini \
  -e "@Environments/lab-test/vars.yml" \
  --become Ansible/playbooks/fix_worker_kubelet.yml
```

#### 5. HAProxy VIP Not Accessible

```bash
# Check VIP assignment
vagrant ssh haproxy1 -c "ip addr show | grep 192.168.56.150"

# Check Keepalived status
vagrant ssh haproxy1 -c "systemctl status keepalived"

# View Keepalived config
vagrant ssh haproxy1 -c "cat /etc/keepalived/keepalived.conf"
```

#### 6. Connectivity Issues

```bash
# Test connectivity from master to HAProxy
vagrant ssh master1 -c "curl -k https://192.168.56.150:6443/healthz"

# Check network interfaces
vagrant ssh haproxy1 -c "ip addr show"
```

---

## 📚 Additional Resources

### Documentation Files

- `VIP_FIX_COMPLETE.md` - VIP functionality fix guide
- `Environments/lab-test/README.md` - Environment-specific documentation

### Useful Commands

```bash
# Check VM status
vagrant status

# SSH into a VM
vagrant ssh master1
vagrant ssh haproxy1

# View cluster logs
vagrant ssh master1 -c "journalctl -u kubelet -n 50"

# Check backup status
vagrant ssh master1 -c "crontab -l"
vagrant ssh master1 -c "ls -lh /opt/backups/k8s/"
```

---

## 🎓 Getting Help

### Check Logs

```bash
# Ansible playbook logs
tail -f /tmp/ansible.log

# Kubespray deployment logs
tail -f /tmp/kubespray.log

# Service logs
vagrant ssh master1 -c "journalctl -u kubelet"
```

### Validate Configuration

```bash
# Validate vars.yml
./script.sh validate

# Check cluster status
./script.sh status

# Test connectivity
./script.sh validate
```

---

## 🔐 Security Notes

- **SSH Keys**: Uses Vagrant's insecure private key for local development
- **Passwords**: Default passwords are in `vars.yml` (change for production)
- **OIDC**: Configure OIDC settings in `vars.yml` for production
- **Certificates**: Managed automatically by Kubespray

---

## 📝 Notes

- **Cluster Name**: Must match the environment folder name (e.g., `lab-test`)
- **Network Prefix**: Used for interface detection and VIP assignment
- **VIP Configuration**: Ensure VIPs don't conflict with node IPs
- **Backup Paths**: Defaults to `/opt/backups/k8s/` (configurable in `vars.yml`)

---

## 🚀 Next Steps

After successful deployment:

1. **Access the Dashboard**: `kubectl proxy` then visit `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/`

2. **Deploy Applications**: Use the cluster API endpoint or Ingress

3. **Monitor Backups**: Check `/opt/backups/k8s/` on master nodes

4. **Scale Cluster**: Add more nodes by updating `vars.yml` and re-running inventory generation

---

**Last Updated**: 2025-11-06  
**Version**: 1.0.0

