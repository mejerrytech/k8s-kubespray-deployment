#!/bin/bash

# ==============================================================================
# KUBERNETES CLUSTER CLEANUP SCRIPT
# ==============================================================================
# This script completely removes Kubernetes from all cluster nodes
# Use with EXTREME CAUTION - this is destructive and irreversible!
# ==============================================================================

set -euo pipefail

# Script metadata
SCRIPT_NAME="Kubernetes Cluster Cleanup"
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
INVENTORY_DIR="${PROJECT_ROOT}/Kubespray/inventory/${CLUSTER_NAME,,}"

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

print_header() {
    echo -e "${RED}======================================================================${NC}"
    echo -e "${YELLOW}  ⚠️  ${SCRIPT_NAME} v${SCRIPT_VERSION} ⚠️${NC}"
    echo -e "${RED}======================================================================${NC}"
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
# CLEANUP FUNCTION
# ==============================================================================

cleanup_cluster() {
    print_header
    
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    ⚠️  DANGER ZONE ⚠️                          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}You are about to COMPLETELY DESTROY the following cluster:${NC}"
    echo ""
    echo -e "  ${CYAN}Cluster Name:${NC} ${CLUSTER_NAME}"
    echo -e "  ${CYAN}Inventory:${NC} ${INVENTORY_DIR}/inventory.ini"
    echo ""
    echo -e "${RED}This will:${NC}"
    echo "  • Stop all Kubernetes services (kubelet, etcd, containerd, etc.)"
    echo "  • Remove ALL Kubernetes data and configuration"
    echo "  • Delete ALL pods, deployments, and volumes"
    echo "  • Reset ALL nodes to pre-Kubernetes state"
    echo "  • Clean iptables and networking rules"
    echo ""
    echo -e "${YELLOW}This action is IRREVERSIBLE and CANNOT be undone!${NC}"
    echo ""
    
    # Check if inventory exists
    if [[ ! -f "$INVENTORY_DIR/inventory.ini" ]]; then
        print_error "Inventory file not found: $INVENTORY_DIR/inventory.ini"
        print_info "Cannot proceed without inventory file"
        exit 1
    fi
    
    # # First confirmation
    # echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    # read -p "$(echo -e ${YELLOW}Type the cluster name \"${CLUSTER_NAME}\" to confirm: ${NC})" confirm_name
    # echo ""
    
    # if [[ "$confirm_name" != "$CLUSTER_NAME" ]]; then
    #     print_info "Cluster name mismatch. Cleanup cancelled."
    #     exit 0
    # fi
    
    # Second confirmation
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    read -p "$(echo -e ${RED}Are you ABSOLUTELY SURE you want to destroy this cluster? Type YES in capital letters: ${NC})" confirm_yes
    echo ""
    
    if [[ "$confirm_yes" != "YES" ]]; then
        print_info "Cleanup cancelled by user."
        exit 0
    fi
    
    # # Third and final confirmation
    # echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    # read -p "$(echo -e ${RED}FINAL WARNING: This will PERMANENTLY DELETE all cluster data. Type \"DELETE\" to proceed: ${NC})" confirm_delete
    # echo ""
    
    # if [[ "$confirm_delete" != "DELETE" ]]; then
    #     print_info "Cleanup cancelled by user."
    #     exit 0
    # fi
    
    # Setup logging
    LOG_FILE="/tmp/k8s-cleanup-${CLUSTER_NAME}-$(date +%Y%m%d-%H%M%S).log"
    exec > >(tee -a "$LOG_FILE") 2>&1
    
    echo ""
    print_warning "Proceeding with cluster destruction..."
    print_info "Cleanup log: $LOG_FILE"
    echo ""
    sleep 3
    
    # Run cleanup playbook
    cd "$PROJECT_ROOT"
    
    print_step "Executing cleanup playbook on all cluster nodes..."
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        "$PROJECT_ROOT/Ansible/playbooks/cleanup_cluster.yml"
    
    if [[ $? -eq 0 ]]; then
        echo ""
        print_success "✅ Cluster cleanup completed successfully"
        echo ""
        print_info "All nodes have been reset to pre-Kubernetes state"
        print_info "Waiting 10 seconds for services to stabilize..."
        sleep 10
        echo ""
        print_success "Cleanup log saved: $LOG_FILE"
        echo ""
        echo -e "${GREEN}You can now redeploy the cluster using:${NC}"
        echo -e "  ${CYAN}cd ${SCRIPT_DIR}${NC}"
        echo -e "  ${CYAN}./script.sh deploy${NC}"
        echo ""
    else
        echo ""
        print_error "❌ Cluster cleanup failed"
        print_info "Check the log for details: $LOG_FILE"
        exit 1
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    # Check if Ansible is installed
    if ! command -v ansible-playbook &> /dev/null; then
        print_error "Ansible is not installed or not in PATH"
        exit 1
    fi
    
    # Run cleanup
    cleanup_cluster
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi