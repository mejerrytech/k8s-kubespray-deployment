# 🚀 Kubernetes Multi-Cluster Automation with Kubespray

Production-ready Kubernetes deployment automation framework built on **Kubespray v2.29.0** for on-premises infrastructure with integrated HAProxy load balancing, automated backups, and complete lifecycle management.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Access Points](#-access-points)
- [Troubleshooting](#-troubleshooting)
- [Additional Resources](#-additional-resources)

---

## ✨ Features

- **🏗️ Complete Kubernetes Deployment** - Automated cluster deployment using Kubespray v2.29.0
- **⚖️ Integrated Load Balancing** - HAProxy with Keepalived for high availability
- **📋 Unified Inventory Generation** - Single script creates both Kubespray and HAProxy inventories
- **🎯 Multi-Environment Support** - Lab, Dev, and Production environments
- **💾 Automated Backups** - Scheduled etcd and Kubernetes namespace backups
- **🔧 Maintenance Tasks** - Automated etcd defragmentation and health checks
- **🔐 OIDC Authentication** - Integrated ADFS authentication support
- **📊 Platform Services** - Metrics Server, Kubernetes Dashboard, and NGINX Ingress included
- **🔄 Multi-Platform Support** - Works on vSphere, AWS EKS, Azure AKS

---

## 🔧 Prerequisites

### Infrastructure Requirements

- **vSphere Environment**: Pre-provisioned VMs with:
  - CentOS 7 or Rocky Linux 9 / AlmaLinux 9
  - SSH access configured
  - Passwordless sudo for deployment user
  - DNS resolution for all hostnames

- **Network Requirements**:
  - Static IP addresses for all nodes
  - Network connectivity between all nodes
  - Internet access for package downloads (or local mirror)
  - Reserved VIPs for API server and Ingress

### Node Requirements

**Master Nodes:**
- 4 CPU cores minimum
- 8GB RAM minimum
- 50GB disk space

**Worker Nodes:**
- 2 CPU cores minimum
- 4GB RAM minimum
- 50GB disk space

**HAProxy Nodes:**
- 2 CPU cores
- 2GB RAM
- 20GB disk space

### Control Machine Requirements

**Required Software:**
```bash
# Python 3.9+
python3 --version

# Ansible 2.15+
ansible --version

# Git
git --version

# SSH client with key-based authentication
ssh -V
```

**Install Dependencies:**
```bash
# On RHEL/CentOS/Rocky/AlmaLinux
sudo dnf install -y python3 python3-pip git ansible

# Install Python dependencies
pip3 install pyyaml
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mejerrytech/k8s-kubespray-deployment.git
cd k8s-kubespray-deployment
```

### 2. Configure Your Environment

```bash
cd Environments/lab-test
cp vars.yml vars.yml.example  # Keep a backup

# Edit vars.yml with your infrastructure details
vim vars.yml
```

**Key configurations to update:**
- Cluster name
- Node hostnames and IP addresses
- Network configuration (VIPs, CIDR ranges)
- SSH credentials
- OIDC settings (if enabled)

### 3. Setup SSH Access

Ensure passwordless SSH and sudo access to all nodes:

```bash
# Test SSH access to all nodes
ansible all -i Kubespray/inventory/lab-test/inventory.ini -m ping


### 4. Deploy the Cluster

```bash
cd Environments/lab-test
./script.sh deploy
```

The deployment will automatically:
1. Generate unified inventories
2. Prepare system (kernel modules, sysctl, packages)
3. Deploy Kubernetes cluster via Kubespray
4. Deploy HAProxy load balancers with Keepalived
5. Configure worker and master nodes
6. Setup automated backups and maintenance
7. Validate the deployment

**Typical deployment time:** 20-30 minutes for a complete cluster

---

## 📁 Project Structure

```
k8s-kubespray-deployment/
├── Environments/                       # Environment configurations
│   ├── lab-test/                      # Lab environment
│   ├── dev/                           # Development environment
│   └── prod/                          # Production environment
│       ├── script.sh                  # Main deployment orchestrator
│       ├── vars.yml                   # Environment-specific configuration
│       ├── main.yml                   # Additional configurations
│       └── README.md                  # Environment documentation
├── scripts/
│   └── generate-all-inventories.py    # Unified inventory generator
├── Ansible/
│   ├── inventory/                     # Generated inventory files
│   │   └── haproxy_inventory.ini
│   ├── playbooks/                     # Deployment playbooks
│   │   ├── prepare_kernel_modules.yml
│   │   ├── prepare_system.yml
│   │   ├── deploy_haproxy_keepalived.yml
│   │   ├── fix_worker_kubelet.yml
│   │   ├── fix_cgroup_conf_kubelet.yml
│   │   ├── setup_backup.yml
│   │   ├── setup_maintenance.yml
│   │   └── validate_cluster.yml
│   └── templates/                     # Jinja2 templates
│       ├── backup-etcd.sh.j2
│       ├── backup-k8s-namespaces.sh.j2
│       └── defrag-etcd.sh.j2
├── Kubespray/                         # Kubespray v2.29.0 (submodule)
│   ├── cluster.yml
│   └── inventory/
│       └── lab-test/
└── README.md
```

---

## ⚙️ Configuration

### Environment Configuration (`vars.yml`)

```yaml
# Basic cluster information
cluster_name: k8calab2
environment: lab
datacenter: WTD

# Network configuration
network:
  prefix: "10.13.103"
  gateway: "10.13.103.1"
  netmask: "255.255.255.0"
  dns_servers: ["10.13.2.15"]
  domain: "medimpact.local"
  
  # Virtual IPs
  api_vip: "10.13.103.223"        # Kubernetes API endpoint
  ingress_vip: "10.13.103.232"    # Ingress controller
  virtual_ip: "10.13.103.233"     # Additional VIP
  
  # Kubernetes networking
  cni: "calico"
  service_cidr: "10.236.0.0/16"
  pod_cidr: "10.246.0.0/16"

# Node definitions
nodes:
  masters:
    - hostname: dv1medk8lab2ma01
      ip: "10.13.103.224"
    - hostname: dv1medk8lab2ma02
      ip: "10.13.103.225"
    - hostname: dv1medk8lab2ma03
      ip: "10.13.103.226"
  
  workers:
    - hostname: dv1medk8lab2no01
      ip: "10.13.103.227"
    - hostname: dv1medk8lab2no02
      ip: "10.13.103.228"
    - hostname: dv1medk8lab2no03
      ip: "10.13.103.229"
    - hostname: dv1medk8lab2no04
      ip: "10.13.103.230"
    - hostname: dv1medk8lab2no05
      ip: "10.13.103.231"
  
  haproxy:
    - hostname: dv1medk8lab2proxy1
      ip: "10.13.103.221"
      keepalived_state: MASTER
      keepalived_priority: 200
    - hostname: dv1medk8lab2proxy2
      ip: "10.13.103.222"
      keepalived_state: BACKUP
      keepalived_priority: 100

# HAProxy configuration
haproxy:
  stats_port: 8404
  api_backend_port: 6443
  ingress_http_port: 80
  ingress_https_port: 443

# SSH configuration
ansible:
  user: "kvenkata"
  ssh_private_key_file: "~/.ssh/id_rsa"

# OIDC authentication (optional)
oidc:
  enabled: true
  issuer_url: "https://sts.medimpact.com/adfs"
  client_id: "916d15d5-65f1-481e-9b1a-819c17b8414b"

# Backup configuration
backup:
  enabled: true
  etcd_backup_schedule: "0 4 * * *"       # 4 AM daily
  namespace_backup_schedule: "0 5 * * *"  # 5 AM daily
  retention_days: 7

# Platform services
services:
  metrics_server: true
  kubernetes_dashboard: true
  setup_maintenance: true
```

---

## 🚀 Deployment

### Available Commands

```bash
cd Environments/lab-test

# Full deployment (recommended)
./script.sh deploy

# Individual phases
./script.sh inventory    # Generate inventories only
./script.sh haproxy      # Deploy HAProxy only
./script.sh validate     # Validate cluster health
./script.sh status       # Show cluster status
```

### Deployment Phases

**Phase 1: System Preparation**
- Load required kernel modules (`br_netfilter`, `overlay`, `ip_vs`)
- Configure sysctl parameters for Kubernetes
- Install required packages
- Configure container runtime (containerd)
- Network interface validation

**Phase 2: Kubernetes Cluster Deployment**
- Deploy Kubernetes control plane and workers
- Install CoreDNS for DNS resolution
- Deploy Metrics Server for resource monitoring
- Setup Kubernetes Dashboard
- Configure NGINX Ingress Controller
- Deploy Calico CNI networking

**Phase 3: HAProxy Load Balancer**
- Deploy HAProxy on dedicated nodes
- Configure Keepalived for VIP failover
- Setup load balancing for API server and Ingress
- Configure health checks

**Phase 4: Worker Node Configuration**
- Fix kubelet configuration for correct API endpoint
- Ensure proper cgroup driver configuration

**Phase 5: Cgroup Configuration**
- Apply cgroup configuration to all nodes
- Restart kubelet services

**Phase 6: Backup Setup** (if enabled)
- Deploy etcd backup scripts
- Deploy namespace backup scripts
- Configure cron jobs

**Phase 7: Maintenance Setup** (if enabled)
- Deploy etcd defragmentation scripts
- Configure maintenance cron jobs

**Phase 8: Validation**
- Verify all nodes are Ready
- Check pod status across all namespaces
- Validate VIP accessibility
- Test API server connectivity

---

## 🌐 Access Points

After successful deployment:

| Service | Endpoint | Description |
|---------|----------|-------------|
| **Kubernetes API** | `https://<api_vip>:6443` | Cluster management API |
| **HAProxy Stats** | `http://<api_vip>:8404/stats` | Load balancer dashboard |
| **HTTP Ingress** | `http://<ingress_vip>` | HTTP applications |
| **HTTPS Ingress** | `https://<ingress_vip>` | HTTPS applications |
| **Kubernetes Dashboard** | Via `kubectl proxy` | Web UI for cluster management |

### Accessing the Cluster

```bash
# Copy kubeconfig from first master node
ssh kvenkata@dv1medk8lab2ma01 "sudo cat /etc/kubernetes/admin.conf" > ~/.kube/config

# Or on the master node
mkdir -p ~/.kube
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Verify cluster access
kubectl get nodes
kubectl get pods --all-namespaces

# Access Kubernetes Dashboard
kubectl proxy
# Then visit: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### HAProxy Statistics Dashboard

Access HAProxy stats:
```bash
# View HAProxy statistics
curl http://<api_vip>:8404/stats

# Or in browser
http://<api_vip>:8404/stats
# Username: admin
# Password: <from vars.yml>
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. SSH Connection Failed

```bash
# Test SSH connectivity
ssh -i ~/.ssh/id_rsa kvenkata@dv1medk8lab2ma01

# Check SSH configuration
ansible all -i Kubespray/inventory/lab-test/inventory.ini -m ping
```

#### 2. Passwordless Sudo Not Configured

```bash
# Test sudo access
ssh kvenkata@dv1medk8lab2ma01 "sudo -n whoami"

# If fails, configure passwordless sudo:
# On each node:
sudo visudo -f /etc/sudoers.d/kvenkata
# Add: kvenkata ALL=(ALL) NOPASSWD: ALL
```

#### 3. Network Interface Not Found

```bash
# Check available interfaces on nodes
ansible all -i Kubespray/inventory/lab-test/inventory.ini \
  -m shell -a "ip addr show"

# The playbook will auto-detect the primary interface
# No manual configuration needed
```

#### 4. Kubespray Deployment Fails

```bash
# Check cluster status
kubectl get nodes

# View kubelet logs on a node
ssh kvenkata@dv1medk8lab2ma01 "sudo journalctl -u kubelet -n 100"

# Retry deployment from checkpoint
cd Environments/lab-test
./script.sh deploy
```

#### 5. Worker Nodes Not Ready

```bash
# Check node status
kubectl get nodes -o wide

# Manually run worker node fix
ansible-playbook -i Kubespray/inventory/lab-test/inventory.ini \
  -e "@Environments/lab-test/vars.yml" \
  --become Ansible/playbooks/fix_worker_kubelet.yml
```

#### 6. VIP Not Accessible

```bash
# Check VIP assignment on HAProxy nodes
ssh kvenkata@dv1medk8lab2proxy1 "ip addr show | grep <api_vip>"

# Check Keepalived status
ssh kvenkata@dv1medk8lab2proxy1 "sudo systemctl status keepalived"

# View HAProxy status
ssh kvenkata@dv1medk8lab2proxy1 "sudo systemctl status haproxy"

# Check Keepalived logs
ssh kvenkata@dv1medk8lab2proxy1 "sudo journalctl -u keepalived -n 50"
```

#### 7. DNS Resolution Issues

```bash
# Test DNS from nodes
ansible all -i Kubespray/inventory/lab-test/inventory.ini \
  -m shell -a "nslookup registry.k8s.io"

# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

---

## 📚 Additional Resources

### Validation Commands

```bash
# Check all nodes
kubectl get nodes -o wide

# Check all pods
kubectl get pods -A

# Check cluster health
kubectl get componentstatuses

# View cluster info
kubectl cluster-info

# Check etcd health (from master node)
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/ssl/etcd/ca.pem \
  --cert=/etc/kubernetes/ssl/etcd/node-$(hostname).pem \
  --key=/etc/kubernetes/ssl/etcd/node-$(hostname)-key.pem \
  endpoint health
```

### Backup Verification

```bash
# Check backup cron jobs
ssh kvenkata@dv1medk8lab2ma01 "crontab -l"

# List backups
ssh kvenkata@dv1medk8lab2ma01 "ls -lh /opt/backups/k8s/"

# View backup logs
ssh kvenkata@dv1medk8lab2ma01 "cat /var/log/etcd-backup.log"
```

### Maintenance Commands

```bash
# Check etcd defragmentation schedule
ssh kvenkata@dv1medk8lab2ma01 "crontab -l | grep defrag"

# Manual etcd defragmentation
ssh kvenkata@dv1medk8lab2ma01 "sudo /usr/local/bin/defrag-etcd.sh"
```

---

## 🔐 Security Considerations

### Authentication
- SSH key-based authentication required
- Passwordless sudo configured for automation user
- OIDC integration available for Kubernetes API authentication

### Network Security
- All control plane traffic encrypted with TLS
- etcd traffic encrypted
- Network policies can be implemented via Calico

### Secrets Management
- Kubernetes secrets for sensitive data
- etcd encryption at rest (configurable)
- SSH keys stored securely on control machine

### Backup Security
- Backups include sensitive cluster data
- Store backups in secure location
- Implement backup retention policies

---

## 📊 Monitoring and Observability

### Built-in Monitoring
- **Metrics Server**: Resource usage metrics for nodes and pods
- **Kubernetes Dashboard**: Web UI for cluster monitoring
- **HAProxy Stats**: Load balancer statistics and health

### Integration Ready
- Prometheus (configure in Kubespray)
- Grafana (configure in Kubespray)
- ELK/EFK stack for logging
- Custom monitoring solutions

---

## 🔄 Cluster Management

### Scaling the Cluster

**Add Worker Nodes:**
1. Provision new VMs
2. Add nodes to `vars.yml`
3. Regenerate inventories: `./script.sh inventory`
4. Run Kubespray scale playbook:
```bash
cd Kubespray
ansible-playbook -i inventory/lab-test/inventory.ini scale.yml
```

**Add Master Nodes:**
1. Follow Kubespray documentation for control plane scaling
2. Update HAProxy backend configuration
3. Restart HAProxy services

### Upgrading Kubernetes

```bash
# Update Kubespray to desired version
cd Kubespray
git fetch --tags
git checkout v2.XX.X

# Run upgrade playbook
ansible-playbook -i inventory/lab-test/inventory.ini upgrade-cluster.yml
```

---

## 📝 Best Practices

1. **Always backup etcd before major changes**
   ```bash
   ssh kvenkata@dv1medk8lab2ma01 "sudo /usr/local/bin/backup-etcd.sh"
   ```

2. **Test changes in lab environment first**
   - Deploy to lab-test environment
   - Validate thoroughly
   - Then promote to production

3. **Monitor cluster health regularly**
   ```bash
   kubectl get nodes
   kubectl get pods -A
   kubectl top nodes
   ```

4. **Keep documentation updated**
   - Document any custom configurations
   - Maintain runbooks for common operations
   - Update vars.yml with infrastructure changes

5. **Regular maintenance**
   - Review backup logs
   - Monitor disk space
   - Check certificate expiration
   - Review security updates

---

## 🆘 Support and Contribution

### Getting Help

1. Check this README and environment-specific documentation
2. Review deployment logs in `/tmp/`
3. Check Kubespray documentation: https://kubespray.io/
4. Review Ansible playbook output for specific errors

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly in lab environment
4. Submit pull request with clear description

---

## 📋 Deployment Checklist

Before deploying:
- [ ] VMs provisioned and accessible
- [ ] DNS resolution configured
- [ ] Static IPs assigned
- [ ] Passwordless sudo configured
- [ ] SSH key-based authentication working
- [ ] vars.yml updated with correct values
- [ ] Network CIDRs don't conflict
- [ ] VIPs reserved and not in use
- [ ] Internet access available (or local mirrors configured)
- [ ] Backup of existing cluster (if applicable)

---

**Repository**: https://github.com/mejerrytech/k8s-kubespray-deployment  
**Documentation**: See `Environments/<env>/README.md` for environment-specific details  
