#!/usr/bin/env python3
"""
Unified Inventory Generator
Generates both Kubespray and HAProxy inventories simultaneously
Fully automated with dynamic VM discovery and environment awareness
"""

import os
import sys
import yaml
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class UnifiedInventoryGenerator:
    """Generates both Kubespray and HAProxy inventories for any environment"""
    
    def __init__(self, environment: str):
        self.environment = environment.lower()
        self.environment_title = environment.title()
        
        # Setup paths
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.kubespray_root = self.project_root / "Kubespray"
        self.clusters_dir = self.project_root / "clusters"
        self.environment_dir = self.project_root / "Environments" / self.environment  # Use lowercase for actual directory
        
        # Inventory paths
        self.kubespray_inventory_dir = self.kubespray_root / "inventory" / self.environment
        self.ansible_inventory_dir = self.project_root / "Ansible" / "inventory"
        
        self.print_header()
    
    def print_header(self):
        """Print script header"""
        print("=" * 80)
        print(f"🚀 UNIFIED INVENTORY GENERATOR")
        print(f"📁 Environment: {self.environment_title}")
        print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
    
    def print_step(self, message: str):
        """Print step message"""
        print(f"[STEP] {message}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ [SUCCESS] {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  [WARNING] {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ [ERROR] {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  [INFO] {message}")

    def load_environment_config(self) -> Dict:
        """Load environment configuration from vars.yml"""
        vars_file = self.environment_dir / "vars.yml"
        if vars_file.exists():
            with open(vars_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                self.print_success(f"Loaded environment config from {vars_file}")
                return config
        else:
            self.print_warning(f"Environment config not found: {vars_file}")
            return {}
    
    def get_vm_names_from_config(self, config: Dict) -> List[str]:
        """Extract VM names from vars.yml configuration"""
        vm_names = []
        nodes_config = config.get('nodes', {})
        
        # Get master node hostnames
        for master in nodes_config.get('masters', []):
            if isinstance(master, dict) and 'hostname' in master:
                vm_names.append(master['hostname'])
        
        # Get worker node hostnames
        for worker in nodes_config.get('workers', []):
            if isinstance(worker, dict) and 'hostname' in worker:
                vm_names.append(worker['hostname'])
        
        # Get HAProxy node hostnames
        for haproxy in nodes_config.get('haproxy', []):
            if isinstance(haproxy, dict) and 'hostname' in haproxy:
                vm_names.append(haproxy['hostname'])
        
        return vm_names
    
    def discover_vm_ips(self, config: Dict) -> Dict[str, str]:
        """Discover actual IPs of VMs via SSH (for environments where IPs might change)
        
        Note: In production, IPs are typically static and defined in vars.yml.
        This function is kept for future dynamic discovery needs.
        """
        discovered_ips = {}
        
        # For production environments with static IPs, skip discovery
        # IPs are defined in vars.yml and used directly
        self.print_info("Using static IP configuration from vars.yml")
        
        return discovered_ips
    
    def get_environment_defaults(self, config: Dict) -> Dict[str, str]:
        """Get default IP assignments from vars.yml or calculate from network prefix"""
        defaults = {}
        nodes_config = config.get('nodes', {})
        network_config = config.get('network', {})
        network_prefix = network_config.get('prefix', '192.168.56')
        
        # Extract IPs from nodes configuration
        for master in nodes_config.get('masters', []):
            if isinstance(master, dict) and 'hostname' in master and 'ip' in master:
                defaults[master['hostname']] = master['ip']
        
        for worker in nodes_config.get('workers', []):
            if isinstance(worker, dict) and 'hostname' in worker and 'ip' in worker:
                defaults[worker['hostname']] = worker['ip']
        
        for haproxy in nodes_config.get('haproxy', []):
            if isinstance(haproxy, dict) and 'hostname' in haproxy and 'ip' in haproxy:
                defaults[haproxy['hostname']] = haproxy['ip']
        
        # Get virtual IP from network config
        if 'virtual_ip' in network_config:
            defaults['virtual_ip'] = network_config['virtual_ip']
        elif 'api_vip' in network_config:
            defaults['virtual_ip'] = network_config['api_vip']
        
        return defaults
    
    def generate_kubespray_inventory(self, config: Dict, discovered_ips: Dict[str, str]) -> bool:
        """Generate Kubespray inventory"""
        self.print_step("Generating Kubespray inventory...")
        
        try:
            # Create inventory directory structure
            self.kubespray_inventory_dir.mkdir(parents=True, exist_ok=True)
            (self.kubespray_inventory_dir / "group_vars").mkdir(exist_ok=True)
            
            # Get node IPs (discovered or defaults)
            defaults = self.get_environment_defaults(config)
            nodes_config = config.get('nodes', {})
            
            # Build node information dynamically from vars.yml
            nodes = {}
            
            # Process master nodes
            for master in nodes_config.get('masters', []):
                if isinstance(master, dict) and 'hostname' in master:
                    node_name = master['hostname']
                    # Priority: discovered > config > defaults
                    ip = (discovered_ips.get(node_name) or 
                          master.get('ip') or 
                          defaults.get(node_name))
                    
                    if ip:
                        nodes[node_name] = {
                            'ip': ip,
                            'user': config.get('ansible', {}).get('user', 'root')
                        }
            
            # Process worker nodes
            for worker in nodes_config.get('workers', []):
                if isinstance(worker, dict) and 'hostname' in worker:
                    node_name = worker['hostname']
                    # Priority: discovered > config > defaults
                    ip = (discovered_ips.get(node_name) or 
                          worker.get('ip') or 
                          defaults.get(node_name))
                    
                    if ip:
                        nodes[node_name] = {
                            'ip': ip,
                            'user': config.get('ansible', {}).get('user', 'root')
                        }
            
            if not nodes:
                self.print_error("No valid node configuration found")
                return False
            
            # Generate inventory.ini
            inventory_content = self._generate_kubespray_inventory_content(nodes, config)
            inventory_file = self.kubespray_inventory_dir / "inventory.ini"
            
            with open(inventory_file, 'w') as f:
                f.write(inventory_content)
            
            # Generate group_vars files
            self._generate_kubespray_group_vars(config)
            
            self.print_success(f"Kubespray inventory generated: {inventory_file}")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to generate Kubespray inventory: {e}")
            return False
    
    def _generate_kubespray_inventory_content(self, nodes: Dict, config: Dict) -> str:
        """Generate Kubespray inventory.ini content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Identify master and worker nodes from config
        nodes_config = config.get('nodes', {})
        master_hostnames = set()
        worker_hostnames = set()
        
        for master in nodes_config.get('masters', []):
            if isinstance(master, dict) and 'hostname' in master:
                master_hostnames.add(master['hostname'])
        
        for worker in nodes_config.get('workers', []):
            if isinstance(worker, dict) and 'hostname' in worker:
                worker_hostnames.add(worker['hostname'])
        
        content = f"""# Kubespray Inventory for {self.environment_title} Environment
    # Generated on: {timestamp}
    # DO NOT EDIT MANUALLY - Generated by unified inventory script

    [all]
    """
        
        # Get SSH key from vars.yml configuration
        ansible_config = config.get('ansible', {})
        ssh_key_path = ansible_config.get('ssh_private_key_file', '~/.ssh/id_rsa')
        
        # Add all nodes with SSH configuration
        for node_name, node_info in nodes.items():
            # Use hostname for ansible_host (DNS/hosts file resolves it)
            # Keep IPs for Kubernetes internal networking
            content += f'{node_name} ansible_host={node_name} ansible_user={node_info["user"]} ansible_ssh_private_key_file="{ssh_key_path}" ansible_python_interpreter=/usr/bin/python3 ip={node_info["ip"]} access_ip={node_info["ip"]}\n'
        
        content += "\n[kube_control_plane]\n"
        # Add all master nodes dynamically
        for node_name in nodes.keys():
            if node_name in master_hostnames:
                content += f"{node_name}\n"
        
        content += "\n[etcd]\n"
        # etcd runs on control plane nodes
        for node_name in nodes.keys():
            if node_name in master_hostnames:
                content += f"{node_name}\n"
        
        content += "\n[kube_node]\n"
        # Add all worker nodes dynamically
        for node_name in nodes.keys():
            if node_name in worker_hostnames:
                content += f"{node_name}\n"
        
        content += """\n[calico_rr]

    [k8s_cluster:children]
    kube_control_plane
    kube_node
    calico_rr

    [all:vars]
    # SSH authentication using keys (passwordless sudo must be configured on VMs)
    ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    # Note: Passwordless sudo must be configured on all nodes for automation
    # Example: sudo visudo -f /etc/sudoers.d/kvenkata
    #          Add line: kvenkata ALL=(ALL) NOPASSWD: ALL
    """
        
        return content

    
    def _validate_network_configuration(self, config: Dict) -> bool:
        """Validate network configuration for conflicts and consistency"""
        try:
            network_config = config.get('network', {})
            nodes_config = config.get('nodes', {})
            
            # Get all configured IPs
            node_ips = []
            
            # Master node IPs
            for master in nodes_config.get('masters', []):
                if 'ip' in master:
                    node_ips.append(master['ip'])
            
            # Worker node IPs
            for worker in nodes_config.get('workers', []):
                if 'ip' in worker:
                    node_ips.append(worker['ip'])
            
            # HAProxy node IPs
            for haproxy in nodes_config.get('haproxy', []):
                if 'ip' in haproxy:
                    node_ips.append(haproxy['ip'])
            
            # Virtual IPs
            virtual_ips = []
            if 'api_vip' in network_config:
                virtual_ips.append(network_config['api_vip'])
            if 'ingress_vip' in network_config:
                virtual_ips.append(network_config['ingress_vip'])
            
            # Check for duplicates
            all_ips = node_ips + virtual_ips
            duplicates = [ip for ip in set(all_ips) if all_ips.count(ip) > 1]
            
            if duplicates:
                self.print_error(f"Duplicate IP addresses found: {duplicates}")
                return False
            
            # Check that virtual IPs don't conflict with node IPs
            conflicts = set(node_ips) & set(virtual_ips)
            if conflicts:
                self.print_error(f"Virtual IPs conflict with node IPs: {conflicts}")
                return False
            
            # Validate network ranges don't overlap with host network
            service_cidr = network_config.get('service_cidr', '10.233.0.0/18')
            pod_cidr = network_config.get('pod_cidr', '10.233.64.0/18')
            host_prefix = network_config.get('prefix', '192.168.56')
            
            # Check that service/pod networks don't conflict with host network
            if service_cidr.startswith(host_prefix) or pod_cidr.startswith(host_prefix):
                self.print_error(f"Kubernetes networks conflict with host network {host_prefix}.x")
                return False
            
            self.print_success("Network configuration validation passed")
            return True
            
        except Exception as e:
            self.print_error(f"Network validation error: {e}")
            return False

    def _validate_yaml_syntax(self, file_path: Path) -> bool:
        """Validate that the generated YAML file has correct syntax"""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.print_error(f"YAML syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            self.print_error(f"Error validating {file_path}: {e}")
            return False

    def _generate_kubespray_group_vars(self, config: Dict):
        """Generate Kubespray group_vars files with network configuration from vars.yml
        
        This function now reads network interface configuration from vars.yml:
        - network.interface_config.cluster_interface: Network interface to use (default: enp0s8)
        - network.interface_config.force_cluster_network: Whether to enforce cluster network usage
        
        This fixes the worker node join issue where Kubespray might use NAT interface
        (10.0.2.15) instead of cluster network (192.168.56.x) for API server communication.
        """
        group_vars_dir = self.kubespray_inventory_dir / "group_vars"
        
        # Get network interface configuration from vars.yml
        network_config = config.get('network', {})
        interface_config = network_config.get('interface_config', {})
        cluster_interface = interface_config.get('cluster_interface', 'enp0s8')  # Default for VirtualBox
        force_cluster_network = interface_config.get('force_cluster_network', True)
        
        # Get master IP for network configuration (needed throughout)
        master_ip = None
        nodes_config = config.get('nodes', {})
        if nodes_config.get('masters'):
            master_list = nodes_config['masters']
            if isinstance(master_list, list) and len(master_list) > 0:
                master_data = master_list[0]
                if isinstance(master_data, dict) and 'ip' in master_data:
                    master_ip = master_data['ip']
        
        # Fallback: use network prefix to calculate default
        if not master_ip:
            network_config = config.get('network', {})
            network_prefix = network_config.get('prefix', '192.168.56')
            master_ip = f"{network_prefix}.153"  # Default to .153 for first master
            self.print_warning(f"Using calculated master IP: {master_ip}")
        
        # For certificate generation, we need actual IPs, not Ansible templates
        # Get all node IPs for certificate SAN entries
        node_ips = []
        if 'masters' in nodes_config:
            masters = nodes_config['masters']
            if isinstance(masters, dict):
                for master_config in masters.values():
                    if 'ip' in master_config:
                        node_ips.append(master_config['ip'])
            elif isinstance(masters, list):
                for master_config in masters:
                    if 'ip' in master_config:
                        node_ips.append(master_config['ip'])

        # Note: We do NOT add worker IPs here because etcd only runs on master nodes
        
        # if 'workers' in nodes_config:
        #     workers = nodes_config['workers']
        #     if isinstance(workers, dict):
        #         for worker_config in workers.values():
        #             if 'ip' in worker_config:
        #                 node_ips.append(worker_config['ip'])
        #     elif isinstance(workers, list):
        #         for worker_config in workers:
        #             if 'ip' in worker_config:
        #                 node_ips.append(worker_config['ip'])
        
        # Get services configuration from vars.yml
        services_config = config.get('services', {})
        haproxy_config = config.get('haproxy', {})
        
        # k8s_cluster.yml with enabled addons - read from vars.yml
        k8s_cluster_vars = {
            # Core Kubernetes settings - let Kubespray use its default version if not specified
            'cluster_name': config.get('cluster', {}).get('name', f'k8s-{self.environment}'),
            'kube_network_plugin': network_config.get('cni', 'calico'),  # Use CNI from vars.yml
            'dns_domain': f'{self.environment}.local',
            'download_run_once': False,
            'download_localhost': False,
            'ansible_become': True,
            
            # Network configuration from vars.yml
            'kube_service_addresses': network_config.get('service_cidr', '10.233.0.0/18'),
            'kube_pods_subnet': network_config.get('pod_cidr', '10.233.64.0/18'),
            
            # Service enablement from vars.yml (default to True if not specified)
            # Check both 'deploy_helm' and 'helm_enabled' for backwards compatibility
            'helm_enabled': services_config.get('deploy_helm', services_config.get('helm_enabled', True)),
            'metrics_server_enabled': services_config.get('deploy_metrics_server', services_config.get('metrics_server_enabled', True)),
            'ingress_nginx_enabled': services_config.get('deploy_ingress', services_config.get('ingress_enabled', True)),
            'dashboard_enabled': services_config.get('deploy_dashboard', services_config.get('dashboard_enabled', True)),
            
            # DNS settings
            'dns_mode': 'coredns',
            'enable_nodelocaldns': False,
            
            # RBAC settings  
            'rbac_enabled': services_config.get('deploy_rbac', True),
            'authorization_modes': ['Node', 'RBAC'],
            
            # Ingress controller settings
            'ingress_nginx_host_network': False,
            'ingress_nginx_nodeselector': {},
            'ingress_nginx_namespace': 'ingress-nginx',
            'ingress_nginx_insecure_port': 80,
            'ingress_nginx_secure_port': 443,
            
            # Configure ingress with NodePort for HAProxy
            'ingress_nginx_service_type': 'NodePort',
            'ingress_nginx_nodeport_http': haproxy_config.get('ingress_http_nodeport', 30080),
            'ingress_nginx_nodeport_https': haproxy_config.get('ingress_https_nodeport', 30443),
        }
        
        # Add OIDC configuration if provided
        oidc_config = config.get('oidc', {})
        if oidc_config.get('enabled', False):
            k8s_cluster_vars.update({
                'kube_oidc_auth': True,
                'kube_oidc_url': oidc_config.get('issuer_url', ''),
                'kube_oidc_client_id': oidc_config.get('client_id', ''),
                'kube_oidc_username_claim': oidc_config.get('username_claim', 'username'),
                'kube_oidc_username_prefix': oidc_config.get('username_prefix', 'oidc:'),
                'kube_oidc_groups_claim': oidc_config.get('groups_claim', 'groups'),
            })
            if oidc_config.get('groups_prefix'):
                k8s_cluster_vars['kube_oidc_groups_prefix'] = oidc_config.get('groups_prefix')
            if oidc_config.get('ca_file'):
                k8s_cluster_vars['kube_oidc_ca_file'] = oidc_config.get('ca_file')
        
        # Add network configuration if force_cluster_network is enabled
        if force_cluster_network:
            # Get the master node IP for API server configuration
            master_ip = None
            nodes_config = config.get('nodes', {})
            for master in nodes_config.get('masters', []):
                if 'ip' in master:
                    master_ip = master['ip']
                    break
            
            if not master_ip:
                # Fallback: calculate from network prefix
                network_config = config.get('network', {})
                network_prefix = network_config.get('prefix', '192.168.56')
                master_ip = f"{network_prefix}.153"
                self.print_warning(f"Using calculated master IP fallback: {master_ip}")
            
            k8s_cluster_vars.update({
                # Network configuration to fix API server endpoint issue
                # Use actual IP instead of Ansible variables to avoid certificate issues
                'kube_apiserver_ip': master_ip,
                'loadbalancer_apiserver': {
                    'address': master_ip,
                    'port': 6443
                }
            })
        
        with open(group_vars_dir / "k8s_cluster.yml", 'w') as f:
            f.write("# Kubespray cluster configuration\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            # Write basic configuration
            f.write("ansible_become: true\n")
            f.write("authorization_modes:\n- Node\n- RBAC\n")
            f.write(f"cluster_name: {k8s_cluster_vars['cluster_name']}\n")
            f.write(f"dashboard_enabled: {str(k8s_cluster_vars['dashboard_enabled']).lower()}\n")
            f.write(f"dns_domain: {k8s_cluster_vars['dns_domain']}\n")
            f.write("dns_mode: coredns\n")
            f.write("download_localhost: false\n")
            f.write("download_run_once: false\n")
            f.write("enable_nodelocaldns: false\n")
            f.write(f"helm_enabled: {str(k8s_cluster_vars['helm_enabled']).lower()}\n")
            f.write(f"ingress_nginx_enabled: {str(k8s_cluster_vars['ingress_nginx_enabled']).lower()}\n")
            f.write("ingress_nginx_host_network: false\n")
            f.write("ingress_nginx_insecure_port: 80\n")
            f.write("ingress_nginx_namespace: ingress-nginx\n")
            f.write(f"ingress_nginx_nodeport_http: {k8s_cluster_vars['ingress_nginx_nodeport_http']}\n")
            f.write(f"ingress_nginx_nodeport_https: {k8s_cluster_vars['ingress_nginx_nodeport_https']}\n")
            f.write("ingress_nginx_nodeselector: {}\n")
            f.write("ingress_nginx_secure_port: 443\n")
            f.write("ingress_nginx_service_type: NodePort\n")
            f.write(f"kube_network_plugin: {k8s_cluster_vars['kube_network_plugin']}\n")  # Use CNI from vars.yml
            # Don't specify kube_version - let Kubespray use its default
            f.write(f"metrics_server_enabled: {str(k8s_cluster_vars['metrics_server_enabled']).lower()}\n")
            f.write(f"rbac_enabled: {str(k8s_cluster_vars['rbac_enabled']).lower()}\n")
            
            # Network ranges from vars.yml
            f.write(f"kube_service_addresses: {k8s_cluster_vars['kube_service_addresses']}\n")
            f.write(f"kube_pods_subnet: {k8s_cluster_vars['kube_pods_subnet']}\n")
            
            # Add kubeadm preflight error handling if specified in vars.yml
            if 'kubeadm_ignore_preflight_errors' in config:
                f.write(f"\n# Kubeadm preflight error handling\n")
                ignore_errors = config['kubeadm_ignore_preflight_errors']
                
                # Check if it's already a list or a string
                if isinstance(ignore_errors, list):
                    f.write("kubeadm_ignore_preflight_errors:\n")
                    for error in ignore_errors:
                        f.write(f"  - {error}\n")
                else:
                    # If it's a string with commas, split it into a list
                    error_list = [e.strip() for e in ignore_errors.split(',')]
                    f.write("kubeadm_ignore_preflight_errors:\n")
                    for error in error_list:
                        f.write(f"  - {error}\n")


            # Add OIDC configuration if enabled
            if k8s_cluster_vars.get('kube_oidc_auth'):
                f.write("\n# OIDC Authentication Configuration\n")
                f.write("kube_oidc_auth: true\n")
                f.write(f"kube_oidc_url: {k8s_cluster_vars.get('kube_oidc_url', '')}\n")
                f.write(f"kube_oidc_client_id: {k8s_cluster_vars.get('kube_oidc_client_id', '')}\n")
                f.write(f"kube_oidc_username_claim: {k8s_cluster_vars.get('kube_oidc_username_claim', 'username')}\n")
                f.write(f"kube_oidc_username_prefix: '{k8s_cluster_vars.get('kube_oidc_username_prefix', 'oidc:')}'\n")
                f.write(f"kube_oidc_groups_claim: {k8s_cluster_vars.get('kube_oidc_groups_claim', 'groups')}\n")
                if k8s_cluster_vars.get('kube_oidc_groups_prefix'):
                    f.write(f"kube_oidc_groups_prefix: {k8s_cluster_vars.get('kube_oidc_groups_prefix')}\n")
                if k8s_cluster_vars.get('kube_oidc_ca_file'):
                    f.write(f"kube_oidc_ca_file: {k8s_cluster_vars.get('kube_oidc_ca_file')}\n")
            
            # Add DNS server configuration from vars.yml
            if network_config.get('dns_servers'):
                f.write("\n# Upstream DNS Servers Configuration\n")
                f.write("upstream_dns_servers:\n")
                for dns_server in network_config['dns_servers']:
                    f.write(f'  - "{dns_server}"\n')
            
            # Add quay.io mirror configuration if provided (fixes connectivity issues)
            quay_image_repo = config.get('quay_image_repo')
            if quay_image_repo:
                f.write("\n# Quay.io Image Repository Configuration\n")
                f.write(f"# Using mirror instead of quay.io to fix connectivity issues\n")
                f.write(f"quay_image_repo: \"{quay_image_repo}\"\n")
            
            # Add registry mirror configuration if provided (for connectivity issues)
            registry_config = config.get('registry', {})
            if registry_config.get('enabled') and registry_config.get('mirrors'):
                f.write("\n# Docker Registry Mirror Configuration\n")
                f.write("docker_registry_mirrors:\n")
                for mirror in registry_config['mirrors']:
                    f.write(f'  - "{mirror}"\n')
                
                # Also configure containerd registry mirrors
                f.write("\n# Containerd Registry Mirrors Configuration\n")
                f.write("containerd_registries_mirrors:\n")
                f.write("  - prefix: docker.io\n")
                f.write("    mirrors:\n")
                for mirror in registry_config['mirrors']:
                    f.write(f'      - host: {mirror}\n')
                    f.write("        capabilities:\n")
                    f.write('          - "pull"\n')
                    f.write('          - "resolve"\n')
                    f.write("        skip_verify: false\n")
            
            # Add network configuration if force_cluster_network is enabled
            if force_cluster_network:
                master_ip = k8s_cluster_vars.get("kube_apiserver_ip")
                if not master_ip:
                    # Calculate from network prefix
                    network_config = config.get('network', {})
                    network_prefix = network_config.get('prefix', '192.168.56')
                    master_ip = f"{network_prefix}.153"
                f.write("\n# Network configuration to fix API server endpoint issue\n")
                f.write("# This prevents the NAT interface (10.0.2.15) from being used\n")
                f.write(f'kube_apiserver_ip: "{master_ip}"\n')
                f.write(f'kube_apiserver_bind_address: "{master_ip}"\n')
                
                # Add etcd configuration with actual IPs for certificate generation
                if node_ips:
                    f.write("\n# etcd configuration with actual IPs for certificate generation\n")
                    f.write("# This prevents template variables in OpenSSL certificate generation\n")
                    # etcd_access_addresses must be a comma-separated string (Kubespray uses .split(',') on it)
                    etcd_addresses_str = ",".join([f"https://{ip}:2379" for ip in node_ips])
                    f.write(f'etcd_access_addresses: "{etcd_addresses_str}"\n')
                    # etcd_cert_alt_names and etcd_cert_alt_ips can be lists
                    f.write("etcd_cert_alt_names:\n")
                    for ip in node_ips:
                        f.write(f'  - "{ip}"\n')
                    f.write("etcd_cert_alt_ips:\n")
                    for ip in node_ips:
                        f.write(f'  - "{ip}"\n')
                
                # Disable external load balancer to prevent lb-apiserver.kubernetes.local issues
                f.write("\n# Disable external load balancer configuration\n")
                f.write("# This prevents timeout issues with lb-apiserver.kubernetes.local\n")
                f.write("loadbalancer_apiserver_localhost: true\n")
                f.write("loadbalancer_apiserver_type: localhost\n")
        
        # For runtime IP resolution, use Ansible templates that work during playbook execution
        # For certificate generation, avoid templates and use actual values
        
        # all.yml - use a hybrid approach
        # Get OS from config or default to ubuntu
        bootstrap_os = config.get('cluster', {}).get('bootstrap_os', 'ubuntu')
        all_vars = {
            'bootstrap_os': bootstrap_os,
            'download_cache_dir': '/tmp/kubespray_cache',
        }
        
        # Instead of using problematic Ansible templates, let Kubespray auto-detect
        # but provide fallbacks for certificate generation
        if force_cluster_network:
            all_vars.update({
                # Don't override ip/access_ip with templates - let Kubespray detect
                # Instead, ensure certificate generation uses actual IPs
                'supplementary_addresses_in_ssl_keys': node_ips if node_ips else [master_ip],
                # Force the cluster network interface to be preferred
                'override_system_hostname': False,
                # Remove kube_override_hostname as it causes undefined variable errors
            })
        
        with open(group_vars_dir / "all.yml", 'w') as f:
            f.write("# Global Kubespray configuration\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            # Get OS from config or default
            bootstrap_os = config.get('cluster', {}).get('bootstrap_os', 'ubuntu')
            f.write(f"bootstrap_os: {bootstrap_os}\n")
            f.write("download_cache_dir: /tmp/kubespray_cache\n")
            
            # Add network configuration if force_cluster_network is enabled
            if force_cluster_network:
                f.write("\n# Network configuration to prefer cluster network interface\n")
                f.write("# Configure for cluster internal communication while preserving internet access\n")
                if node_ips:
                    f.write("fallback_ips:\n")
                    for ip in node_ips:
                        f.write(f'  - "{ip}"\n')
                f.write("override_system_hostname: false\n")
                # Remove the problematic kube_override_hostname that causes undefined variable errors
        
        # Validate generated YAML files
        k8s_cluster_file = group_vars_dir / "k8s_cluster.yml"
        all_file = group_vars_dir / "all.yml"
        
        if self._validate_yaml_syntax(k8s_cluster_file) and self._validate_yaml_syntax(all_file):
            self.print_success("Generated YAML files validated successfully")
        else:
            self.print_error("YAML validation failed - please check the generated files")
    
    def generate_haproxy_inventory(self, config: Dict, discovered_ips: Dict[str, str]) -> bool:
        """Generate HAProxy inventory"""
        self.print_step("Generating HAProxy inventory...")
        
        try:
            # Create ansible inventory directory
            self.ansible_inventory_dir.mkdir(parents=True, exist_ok=True)
            
            # Get HAProxy IPs (discovered or defaults)
            defaults = self.get_environment_defaults(config)
            network_config = config.get('network', {})
            nodes_config = config.get('nodes', {})
            
            # Get HAProxy nodes dynamically from config
            haproxy_nodes = nodes_config.get('haproxy', [])
            if not haproxy_nodes or len(haproxy_nodes) < 2:
                self.print_error("At least 2 HAProxy nodes required in nodes.haproxy")
                return False
            
            haproxy1_node = haproxy_nodes[0]
            haproxy2_node = haproxy_nodes[1]
            haproxy1_name = haproxy1_node.get('hostname', 'haproxy1') if isinstance(haproxy1_node, dict) else 'haproxy1'
            haproxy2_name = haproxy2_node.get('hostname', 'haproxy2') if isinstance(haproxy2_node, dict) else 'haproxy2'
            
            haproxy1_ip = (discovered_ips.get(haproxy1_name) or 
                          (haproxy1_node.get('ip') if isinstance(haproxy1_node, dict) else None) or
                          network_config.get('haproxy1_ip') or 
                          defaults.get(haproxy1_name))
            
            haproxy2_ip = (discovered_ips.get(haproxy2_name) or 
                          (haproxy2_node.get('ip') if isinstance(haproxy2_node, dict) else None) or
                          network_config.get('haproxy2_ip') or 
                          defaults.get(haproxy2_name))
            
            virtual_ip = (network_config.get('virtual_ip') or 
                         network_config.get('api_vip') or
                         defaults.get('virtual_ip'))
            
            if not all([haproxy1_ip, haproxy2_ip, virtual_ip]):
                self.print_error(f"Missing HAProxy IP configuration: haproxy1={haproxy1_ip}, haproxy2={haproxy2_ip}, vip={virtual_ip}")
                return False
            
            # Get keepalived settings from config
            keepalived1_priority = haproxy1_node.get('keepalived_priority', 110) if isinstance(haproxy1_node, dict) else 110
            keepalived1_state = haproxy1_node.get('keepalived_state', 'MASTER') if isinstance(haproxy1_node, dict) else 'MASTER'
            keepalived2_priority = haproxy2_node.get('keepalived_priority', 100) if isinstance(haproxy2_node, dict) else 100
            keepalived2_state = haproxy2_node.get('keepalived_state', 'BACKUP') if isinstance(haproxy2_node, dict) else 'BACKUP'
            
            # Generate HAProxy inventory content
            inventory_content = self._generate_haproxy_inventory_content(
                haproxy1_name, haproxy1_ip, keepalived1_priority, keepalived1_state,
                haproxy2_name, haproxy2_ip, keepalived2_priority, keepalived2_state,
                virtual_ip, config
            )
            
            inventory_file = self.ansible_inventory_dir / "haproxy_inventory.ini"
            with open(inventory_file, 'w') as f:
                f.write(inventory_content)
            
            self.print_success(f"HAProxy inventory generated: {inventory_file}")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to generate HAProxy inventory: {e}")
            return False
    
    def _generate_haproxy_inventory_content(self, haproxy1_name: str, haproxy1_ip: str, 
                                           keepalived1_priority: int, keepalived1_state: str,
                                           haproxy2_name: str, haproxy2_ip: str,
                                           keepalived2_priority: int, keepalived2_state: str,
                                           virtual_ip: str, config: Dict) -> str:
        """Generate HAProxy inventory.ini content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        

        # Get SSH configuration from vars.yml
        ansible_config = config.get('ansible', {})
        ansible_user = ansible_config.get('user', 'root')
        ssh_key_path = ansible_config.get('ssh_private_key_file', '~/.ssh/id_rsa')

        
        haproxy1_host = haproxy1_name  # ← CHANGED
        haproxy2_host = haproxy2_name  # ← CHANGED
        haproxy1_ansible_port = ""
        haproxy2_ansible_port = ""
        self.print_success(f"Using hostnames for SSH: {haproxy1_name}, {haproxy2_name}")
        
        content = f"""# HAProxy Inventory for {self.environment_title} Environment
# Generated on: {timestamp}
# DO NOT EDIT MANUALLY - Generated by unified inventory script

[haproxy]
{haproxy1_name} ansible_host={haproxy1_host} {haproxy1_ansible_port} keepalived_priority={keepalived1_priority} keepalived_state={keepalived1_state} ansible_ssh_private_key_file="{ssh_key_path}"
{haproxy2_name} ansible_host={haproxy2_host} {haproxy2_ansible_port} keepalived_priority={keepalived2_priority} keepalived_state={keepalived2_state} ansible_ssh_private_key_file="{ssh_key_path}"

[haproxy:vars]
ansible_user={ansible_user}
# SSH authentication using keys (passwordless sudo must be configured)
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
virtual_ip={virtual_ip}
env={self.environment}
"""
        
        return content
    
    def validate_generated_inventories(self) -> bool:
        """Validate both generated inventories"""
        self.print_step("Validating generated inventories...")
        
        success = True
        
        # Check Kubespray inventory
        kubespray_inventory = self.kubespray_inventory_dir / "inventory.ini"
        if kubespray_inventory.exists():
            self.print_success("Kubespray inventory file exists")
        else:
            self.print_error("Kubespray inventory file missing")
            success = False
        
        # Check HAProxy inventory
        haproxy_inventory = self.ansible_inventory_dir / "haproxy_inventory.ini"
        if haproxy_inventory.exists():
            self.print_success("HAProxy inventory file exists")
        else:
            self.print_error("HAProxy inventory file missing")
            success = False
        
        return success
    
    def display_summary(self, discovered_ips: Dict[str, str]):
        """Display generation summary"""
        print("\n" + "=" * 80)
        print("📊 INVENTORY GENERATION SUMMARY")
        print("=" * 80)
        
        print(f"Environment: {self.environment_title}")
        # print(f"Discovered VMs: {len(discovered_ips)}")
        
        if discovered_ips:
            print("\n🔍 Discovered IPs:")
            for vm, ip in discovered_ips.items():
                print(f"  • {vm}: {ip}")
        
        print(f"\n📁 Generated Files:")
        print(f"  • Kubespray Inventory: {self.kubespray_inventory_dir}/inventory.ini")
        print(f"  • HAProxy Inventory: {self.ansible_inventory_dir}/haproxy_inventory.ini")
        
        print("\n✅ Ready for deployment!")
        print("=" * 80)
    
    def generate_all(self) -> bool:
        """Generate both inventories"""
        try:
            # Load environment configuration
            config = self.load_environment_config()
            
            # Validate network configuration first
            if not self._validate_network_configuration(config):
                return False
            
            # Discover VM IPs (pass config to get VM names dynamically)
            discovered_ips = self.discover_vm_ips(config)
            
            # Generate both inventories
            kubespray_success = self.generate_kubespray_inventory(config, discovered_ips)
            haproxy_success = self.generate_haproxy_inventory(config, discovered_ips)
            
            # Validate results
            validation_success = self.validate_generated_inventories()
            
            # Display summary
            if kubespray_success and haproxy_success and validation_success:
                self.display_summary(discovered_ips)
                return True
            else:
                self.print_error("Some inventories failed to generate")
                return False
                
        except Exception as e:
            self.print_error(f"Unified inventory generation failed: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate unified Kubespray and HAProxy inventories')
    parser.add_argument('environment', help='Environment name (Lab, Dev, Prod)')
    parser.add_argument('--test', action='store_true', help='Test mode - only validate configuration')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = UnifiedInventoryGenerator(args.environment)
    
    if args.test:
        # Test mode - just validate
        config = generator.load_environment_config()
        discovered_ips = generator.discover_vm_ips(config)
        generator.display_summary(discovered_ips)
        return 0
    
    # Generate inventories
    success = generator.generate_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())