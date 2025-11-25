#!/bin/bash

# ==============================================================================
# KUBERNETES CLUSTER CLEANUP SCRIPT - IMPROVED VERSION
# ==============================================================================
# Two-stage cleanup: Kubespray reset + Forceful custom cleanup
# Use with EXTREME CAUTION - this is destructive and irreversible!
# ==============================================================================

set -euo pipefail

# Script metadata
SCRIPT_NAME="Kubernetes Cluster Cleanup"
SCRIPT_VERSION="2.0.0"
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
    echo "  • Run Kubespray's official reset.yml"
    echo "  • Force kill all containers and processes"
    echo "  • Unmount all kubelet volumes"
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
    
    # Confirmation
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    read -p "$(echo -e ${RED}Are you ABSOLUTELY SURE you want to destroy this cluster? Type YES in capital letters: ${NC})" confirm_yes
    echo ""
    
    if [[ "$confirm_yes" != "YES" ]]; then
        print_info "Cleanup cancelled by user."
        exit 0
    fi
    
    # Setup logging
    LOG_FILE="/tmp/k8s-cleanup-${CLUSTER_NAME}-$(date +%Y%m%d-%H%M%S).log"
    exec > >(tee -a "$LOG_FILE") 2>&1
    
    echo ""
    print_warning "Proceeding with TWO-STAGE cluster destruction..."
    print_info "Cleanup log: $LOG_FILE"
    echo ""
    sleep 3
    
    # Run cleanup - TWO STAGE APPROACH
    cd "$PROJECT_ROOT"
    
    # =========================================================================
    # STAGE 1: KUBESPRAY OFFICIAL RESET
    # =========================================================================
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    print_step "Stage 1: Running Kubespray reset.yml (official cleanup)..."
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e reset_confirmation=yes \
        --become \
        "$PROJECT_ROOT/Kubespray/reset.yml"
    
    KUBESPRAY_EXIT=$?
    
    if [[ $KUBESPRAY_EXIT -ne 0 ]]; then
        echo ""
        print_warning "⚠️  Kubespray reset had issues (exit code: $KUBESPRAY_EXIT)"
        print_info "Continuing with forceful cleanup to ensure everything is removed..."
    else
        echo ""
        print_success "✅ Kubespray reset completed successfully"
    fi
    
    echo ""
    sleep 3
    
    # =========================================================================
    # STAGE 2: FORCEFUL CUSTOM CLEANUP
    # =========================================================================
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    print_step "Stage 2: Running forceful cleanup (ensures complete removal)..."
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    ansible-playbook \
        -i "$INVENTORY_DIR/inventory.ini" \
        -e "@$VARS_FILE" \
        -e "cluster_name=${CLUSTER_NAME}" \
        --become \
        "$PROJECT_ROOT/Ansible/playbooks/cleanup_cluster.yml"
    
    CUSTOM_EXIT=$?
    
    # =========================================================================
    # FINAL RESULT
    # =========================================================================
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    
    if [[ $CUSTOM_EXIT -eq 0 ]]; then
        echo ""
        print_success "✅ Complete cluster cleanup finished successfully"
        echo ""
        print_info "Cleanup stages:"
        print_info "  • Kubespray reset: $([ $KUBESPRAY_EXIT -eq 0 ] && echo '✅ Success' || echo '⚠️  Had issues')"
        print_info "  • Forceful cleanup: ✅ Success"
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
        print_error "❌ Cluster cleanup failed in Stage 2"
        echo ""
        print_info "Cleanup stages:"
        print_info "  • Kubespray reset: $([ $KUBESPRAY_EXIT -eq 0 ] && echo '✅ Success' || echo '⚠️  Had issues')"
        print_info "  • Forceful cleanup: ❌ Failed"
        echo ""
        print_info "Check the log for details: $LOG_FILE"
        echo ""
        print_warning "Manual cleanup may be required"
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