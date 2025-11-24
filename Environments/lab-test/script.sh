#!/bin/bash

# ==============================================================================
# LAB-TEST KUBERNETES CLUSTER DEPLOYMENT SCRIPT
# ==============================================================================
# This script provides a simple interface to deploy, manage, and validate
# the lab-test Kubernetes cluster using the unified automation framework
# ==============================================================================

set -euo pipefail

# Script metadata
SCRIPT_NAME="Kubernetes Cluster Deployment"
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Auto-detect cluster name from environment folder
CLUSTER_NAME="$(basename "${SCRIPT_DIR}")"
export CLUSTER_NAME

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration files
VARS_FILE="${SCRIPT_DIR}/vars.yml"
MAIN_FILE="${SCRIPT_DIR}/main.yml"
INVENTORY_DIR="${PROJECT_ROOT}/Kubespray/inventory/${CLUSTER_NAME,,}"  # lowercase cluster name

# Helper function to read YAML values
get_yaml_value() {
    local key_path="$1"
    python3 -c "
import yaml
import sys
try:
    with open('${VARS_FILE}', 'r') as f:
        config = yaml.safe_load(f)
    keys = '${key_path}'.split('.')
    value = config
    for key in keys:
        value = value.get(key, '')
    print(value if value else '')
except Exception as e:
    sys.exit(1)
" 2>/dev/null || echo ""
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

print_header() {
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${CYAN}  ${SCRIPT_NAME} v${SCRIPT_VERSION}${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

validate_environment() {
    print_step "Validating deployment environment..."
    
    # Check if configuration files exist
    if [[ ! -f "$VARS_FILE" ]]; then
        print_error "Configuration file not found: $VARS_FILE"
        exit 1
    fi
    
    if [[ ! -f "$MAIN_FILE" ]]; then
        print_error "Main configuration file not found: $MAIN_FILE"
        exit 1
    fi
    
    # Check if project root exists
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project root directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    # Check if Ansible is installed
    if ! command -v ansible-playbook &> /dev/null; then
        print_error "Ansible is not installed or not in PATH"
        print_info "Please install Ansible: pip install ansible"
        exit 1
    fi
    
    # Check if Python is installed  
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Environment validation completed"
}

generate_inventory() {
    print_step "Generating unified inventories for ${CLUSTER_NAME}..."
    
    # Create inventory directory structure
    mkdir -p "$INVENTORY_DIR"
    mkdir -p "$INVENTORY_DIR/group_vars"
    
    print_success "Created inventory directory structure for ${CLUSTER_NAME}"
    
    # Run the unified inventory generation script
    cd "$PROJECT_ROOT"
    python3 scripts/generate-all-inventories.py "${CLUSTER_NAME}"
    
    if [[ $? -eq 0 ]]; then
        print_success "Unified inventories generation completed"
        print_info "SSH keys configured individually for each VM"
        
    else
        print_error "Unified inventories generation failed"
        exit 1
    fi
}

# ==============================================================================
# DEPLOYMENT FUNCTIONS
# ==============================================================================

deploy_cluster() {

    print_step "Deploying ${CLUSTER_NAME} Kubernetes cluster with streamlined approach..."
    
    cd "$PROJECT_ROOT"
    
    print_info "🚀 Starting streamlined deployment process"
    echo ""
    
    # Step 1: System preparation
    print_step "Phase 1: System preparation"
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/prepare_kernel_modules.yml
    
    if [[ $? -ne 0 ]]; then
        print_error "Bridge module loading failed"
        exit 1
    fi
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/prepare_system.yml
    
    if [[ $? -ne 0 ]]; then
        print_error "Preflight checks failed"
        exit 1
    fi
    
    print_success "System preparation completed"
    



    # # Step 2: Deploy HAProxy load balancer
    # print_step "Phase 3: HAProxy load balancer deployment"
    # cd "$PROJECT_ROOT"
    
    # ansible-playbook \
    #     -i "Ansible/inventory/haproxy_inventory.ini" \
    #     -e "@$VARS_FILE" \
    #     -e "cluster_name=${CLUSTER_NAME}" \
    #     --become \
    #     Ansible/playbooks/deploy_haproxy_keepalived.yml
    
    # if [[ $? -ne 0 ]]; then
    #     print_error "HAProxy deployment failed"
    #     exit 1
    # fi
    
    # print_success "HAProxy load balancer deployment completed"
    


    # Step 1.5: Fix Kubespray module before deployment
    print_step "Fixing Kubespray kube module..."

    cd "$PROJECT_ROOT/Kubespray/library"

    # Remove any existing kube.py (file or symlink)
    rm -f kube.py

    # Create symlink to the module
    ln -sf ../plugins/modules/kube.py kube.py

    print_success "Kubespray symlink to |  /plugins/modules/kube.py  |  created"
    echo ""




    # Step 2: Deploy Kubernetes with Kubespray (includes all platform services)
    print_step "Phase 2: Kubernetes cluster deployment via Kubespray"
    print_info "This will install: Kubernetes, CoreDNS, Metrics Server, Dashboard, Ingress"
    
    cd "$PROJECT_ROOT/Kubespray"
    ansible-playbook \
        -i "inventory/${CLUSTER_NAME}/inventory.ini" \
        --become \
        cluster.yml \
        -e "dns_domain=${CLUSTER_NAME,,}.local"
    
    if [[ $? -ne 0 ]]; then
        print_error "Kubespray cluster deployment failed"
        exit 1
    fi
    
    print_success "Kubernetes cluster deployment completed"



    # Step 2.5: Setup kubeconfig for users
    print_step "Setting up kubeconfig for non-root users..."

    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        --become \
        Ansible/playbooks/setup_kubeconfig_users.yml

    if [[ $? -eq 0 ]]; then
        print_success "Kubeconfig setup completed"
        print_info "Users can now run 'kubectl get nodes' without --kubeconfig"
    else
        print_warning "Kubeconfig setup had issues"
    fi



    # Step 3: Deploy HAProxy load balancer
    print_step "Phase 3: HAProxy load balancer deployment"
    cd "$PROJECT_ROOT"
    
    ansible-playbook \
        -i "Ansible/inventory/haproxy_inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/deploy_haproxy_keepalived.yml
    
    if [[ $? -ne 0 ]]; then
        print_error "HAProxy deployment failed"
        exit 1
    fi
    
    print_success "HAProxy load balancer deployment completed"


    # Step 4: Fix worker node kubelet configuration
    print_step "Phase 4: Fixing worker node kubelet configuration"
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        -e "api_vip=$(get_yaml_value "network.api_vip")" \
        -e "virtual_ip=$(get_yaml_value "network.virtual_ip")" \
        --become \
        Ansible/playbooks/fix_worker_kubelet.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "Worker node configuration fix completed"
    else
        print_warning "Worker node fix had issues (cluster may still be functional)"
    fi
    
    # Step 5: Fix worker and master node kubelet cgroup configuration
    print_step "Phase 5: Fixing worker and master node kubelet cgroup configuration"
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/fix_cgroup_conf_kubelet.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "Worker and Master node cgroup configuration fix completed"
    else
        print_warning "Worker and Master node cgroup configuration fix had issues (cluster may still be functional)"
    fi

    # Step 6: Deploy Kubernetes Dashboard (if enabled)
    dashboard_enabled=$(get_yaml_value "services.deploy_dashboard")
    if [[ "$dashboard_enabled" == "True" ]] || [[ "$dashboard_enabled" == "true" ]]; then
        print_step "Phase X: Setting up Kubernetes Dashboard with admin access"
        
        ansible-playbook \
            -i "$INVENTORY_DIR/inventory.ini" \
            -e "@$VARS_FILE" \
            -e "cluster_name=${CLUSTER_NAME}" \
            --become \
            Ansible/playbooks/deploy_dashboard.yml
        
        if [[ $? -eq 0 ]]; then
            print_success "Dashboard admin setup completed"
            print_info "Token saved to /root/dashboard-admin-token.txt on first master"
        else
            print_warning "Dashboard setup had issues"
        fi
    else
        print_info "Dashboard setup skipped (services.deploy_dashboard: false)"
    fi

    # Step 7: Setup backups (if enabled)
    backup_enabled=$(get_yaml_value "backup.enabled")
    if [[ "$backup_enabled" == "True" ]] || [[ "$backup_enabled" == "true" ]]; then
        print_step "Phase 5: Setting up automated backups"
        
        ansible-playbook \
            -i "$INVENTORY_DIR/inventory.ini" \
            -e "@$VARS_FILE" \
            -e "cluster_name=${CLUSTER_NAME}" \
            --become \
            Ansible/playbooks/setup_backup.yml
        
        if [[ $? -eq 0 ]]; then
            print_success "Backup setup completed"
        else
            print_warning "Backup setup had issues (backups may not be scheduled)"
        fi
    else
        print_info "Backup setup skipped (backup.enabled: false)"
    fi
    
    # Step 8: Setup maintenance (if enabled)
    maintenance_enabled=$(get_yaml_value "services.setup_maintenance")
    if [[ "$maintenance_enabled" == "True" ]] || [[ "$maintenance_enabled" == "true" ]]; then
        print_step "Phase 6: Setting up maintenance tasks"
        
        ansible-playbook \
            -i "$INVENTORY_DIR/inventory.ini" \
            -e "@$VARS_FILE" \
            -e "cluster_name=${CLUSTER_NAME}" \
            --become \
            Ansible/playbooks/setup_maintenance.yml
        
        if [[ $? -eq 0 ]]; then
            print_success "Maintenance setup completed"
        else
            print_warning "Maintenance setup had issues"
        fi
    else
        print_info "Maintenance setup skipped (services.setup_maintenance: false)"
    fi
    
    # Step 9: Validate deployment
    print_step "Phase 8: Deployment validation"
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        -e "api_vip=$(get_yaml_value "network.api_vip")" \
        -e "ingress_vip=$(get_yaml_value "network.ingress_vip")" \
        -e "virtual_ip=$(get_yaml_value "network.virtual_ip")" \
        --become \
        Ansible/playbooks/validate_cluster.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "Cluster validation completed successfully"
    else
        print_warning "Cluster validation had issues (may be normal for new cluster)"
    fi
    
    # Display success summary
    echo ""
    print_success "🎉 Complete deployment finished!"
    
    # Read VIP from vars.yml
    API_VIP=$(get_yaml_value "network.api_vip")
    VIRTUAL_IP=$(get_yaml_value "network.virtual_ip")
    HAPROXY_STATS_PORT=$(get_yaml_value "haproxy.stats_port")
    
    # Use virtual_ip if available, otherwise fallback to api_vip, otherwise default
    VIP="${VIRTUAL_IP:-${API_VIP:-192.168.56.150}}"
    STATS_PORT="${HAPROXY_STATS_PORT:-8404}"
    
    echo -e "${CYAN}Access Points:${NC}"
    echo "  • Kubernetes API: https://${VIP}:6443"
    echo "  • HAProxy Stats: http://${VIP}:${STATS_PORT}/stats"
    echo "  • HTTP Apps: http://${VIP}"
    echo "  • HTTPS Apps: https://${VIP}"

}

validate_cluster() {
    print_step "Validating ${CLUSTER_NAME} Kubernetes cluster..."
    
    cd "$PROJECT_ROOT"
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        -e "api_vip=$(get_yaml_value "network.api_vip")" \
        -e "ingress_vip=$(get_yaml_value "network.ingress_vip")" \
        -e "virtual_ip=$(get_yaml_value "network.virtual_ip")" \
        --become \
        --become-user=root \
        Ansible/playbooks/validate_cluster.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "Cluster validation completed successfully"
    else
        print_error "Cluster validation failed"
        exit 1
    fi
}

deploy_haproxy_only() {
    print_step "Deploying HAProxy and keepalived for ${CLUSTER_NAME}..."
    
    cd "$PROJECT_ROOT"
    
    # Deploy HAProxy directly using Ansible playbook
    ansible-playbook \
        -i "Ansible/inventory/haproxy_inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/deploy_haproxy_keepalived.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "HAProxy and keepalived deployment completed successfully"
        
        # Read VIP from vars.yml
        API_VIP=$(get_yaml_value "network.api_vip")
        VIRTUAL_IP=$(get_yaml_value "network.virtual_ip")
        HAPROXY_STATS_PORT=$(get_yaml_value "haproxy.stats_port")
        
        # Use virtual_ip if available, otherwise fallback to api_vip, otherwise default
        VIP="${VIRTUAL_IP:-${API_VIP:-192.168.56.150}}"
        STATS_PORT="${HAPROXY_STATS_PORT:-8404}"
        
        echo -e "${CYAN}Access Points:${NC}"
        echo "  • HAProxy Stats: http://${VIP}:${STATS_PORT}/stats"
        echo "  • HTTP Apps: http://${VIP}"
        echo "  • HTTPS Apps: https://${VIP}"
    else
        print_error "HAProxy and keepalived deployment failed"
        exit 1
    fi
}

# ==============================================================================
# CLEANUP FUNCTION
# ==============================================================================

cleanup_cluster() {
    print_step "Cleaning up existing Kubernetes cluster on all nodes..."
    
    cd "$PROJECT_ROOT"
    
    # Confirm cleanup
    echo -e "${Green} Reseting all nodes and removing Kubernetes completely!"

    
    # Run cleanup playbook
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        Ansible/playbooks/cleanup_cluster.yml
    
    if [[ $? -eq 0 ]]; then
        print_success "Cluster cleanup completed successfully"
        echo ""
        print_info "Waiting 10 seconds for services to settle..."
        sleep 10
        echo ""
    else
        print_error "Cluster cleanup failed"
        exit 1
    fi
}

# ==============================================================================
# MENU FUNCTIONS
# ==============================================================================

show_menu() {
    echo ""
    echo -e "${CYAN}🚀 ${CLUSTER_NAME} Kubernetes Deployment Options:${NC}"
    echo "  1) 🏗️  Deploy complete cluster (inventory + Kubespray + HAProxy)"
    echo "  2) ⚖️  Deploy HAProxy only (requires existing cluster)"  
    echo "  3) 📋 Generate inventories only"
    echo "  4) ✅ Validate cluster"
    echo "  5) 📊 Show status"
    echo "  6) 🧹 Cleanup cluster (reset all nodes)"           
    echo "  7) 🔄 Cleanup + Deploy (full reset)"              
    echo "  8) 🚪 Exit"  
    echo ""
}

show_status() {
    print_step "Checking ${CLUSTER_NAME} cluster status..."
    
    # Check if inventory exists
    if [[ -f "$INVENTORY_DIR/inventory.ini" ]]; then
        print_info "Inventory file: EXISTS"
    else
        print_warning "Inventory file: NOT FOUND"
    fi
    
    # Check if HAProxy inventory exists
    if [[ -f "${PROJECT_ROOT}/Ansible/inventory/haproxy_inventory.ini" ]]; then
        print_info "HAProxy inventory file: EXISTS"
    else
        print_warning "HAProxy inventory file: NOT FOUND"
    fi
    
    # Try to connect to cluster
    cd "$PROJECT_ROOT"
    
    if [[ -f "$INVENTORY_DIR/inventory.ini" ]]; then
        ansible all \
            -i "$INVENTORY_DIR/inventory.ini" \
            -m ping \
            --become \
            --one-line 2>/dev/null && print_success "Cluster nodes: REACHABLE" || print_warning "Cluster nodes: NOT REACHABLE"
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    print_header
    
    # Validate environment first
    validate_environment
    
    # If arguments provided, run directly
    if [[ $# -gt 0 ]]; then
        case "$1" in
            "haproxy")
                deploy_haproxy_only
                ;;
            "deploy")
                # Setup logging for deployment
                LOG_FILE="/tmp/k8s-deployment-$(date +%Y%m%d-%H%M%S).log"
                exec > >(tee -a "$LOG_FILE") 2>&1
                print_info "Deployment log: $LOG_FILE"
                echo ""

                # Run deployment
                generate_inventory
                cleanup_cluster
                deploy_cluster
                validate_cluster

                # Log completion message
                echo ""
                print_success "Full deployment log saved: $LOG_FILE"
                ;;
            "cleanup")                                        
                cleanup_cluster
                ;;
            "validate")
                validate_cluster
                ;;
            "inventory")
                generate_inventory
                ;;
            "status")
                show_status
                ;;
            *)
                print_error "Unknown action: $1"
                echo "Usage: $0 [deploy|validate|inventory|status|haproxy]"
                exit 1
                ;;
        esac
        return 0
    fi
    
    # Interactive menu
    while true; do
        show_menu
        read -p "Please select an action (1-6): " choice
        
        case $choice in
            1)
                # Setup logging for deployment
                LOG_FILE="/tmp/k8s-deployment-$(date +%Y%m%d-%H%M%S).log"
                exec > >(tee -a "$LOG_FILE") 2>&1
                print_info "Deployment log: $LOG_FILE"
                echo ""
                
                # Run deployment
                cleanup_cluster
                generate_inventory
                deploy_cluster
                
                # Log completion message
                echo ""
                print_success "Full deployment log saved: $LOG_FILE"
                ;;
            2)
                deploy_haproxy_only
                ;;
            3)
                generate_inventory
                ;;
            4)
                validate_cluster
                ;;
            5)
                show_status
                ;;
            
            6)                                               
                cleanup_cluster
                ;;

            7)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please select 1-6."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi