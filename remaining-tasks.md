# Remaining Conversion Tasks



### Task 1: Time Synchronization 
- **What:** Convert chrony sync commands to Ansible
- **Status:** NOT DONE
- **Credentials:** None needed
- **Deliverable:** `configure_time_sync.yml` playbook

---

### Task 2: MedImpact CA Certificates 
- **What:** Deploy 7 CA certificates from `Terraform-master/RemoteBuildFiles-Active/certs/`
- **Status:** NOT DONE
- **Credentials:** None needed (certificates in repo)
- **Deliverable:** `deploy_certificates.yml` playbook

**Files to deploy:**
- medimpact-root.cer
- medimpact-intermediate-1.cer
- medimpact-intermediate-2.cer
- medimpact-subca1-2019.cer
- medimpact-subca2-2019.cer
- medimpactdirect-root.cer
- medimpactdirect-subca1.cer

---

### Task 3: Active Directory Domain Join 
- **What:** Convert `sssd-joindomain.sh` to Ansible
- **Status:** NOT DONE
- **Credentials:** IN the file as placeholder (vars file placeholders)
- **Deliverable:** `join_domain.yml` playbook with credential variables

---

### Task 4: Security Agents - Trend Micro 
- **What:** Convert 4 DSM installation scripts to Ansible
- **Status:** NOT DONE
- **Credentials:** IN the file as placeholder (vars file placeholders)
- **Deliverable:** `deploy_security_agents.yml` playbook

**Scripts to convert:**
- `mi_install_deep_security.sh`
- `medimpact_trend_cloudone.sh`
- `AgentDeploymentScript_CA.sh`
- `AgentDeploymentScript_AZ.sh`

---

### Task 5: Monitoring Stack Deployment 
- **What:** Automate deployment of EXISTING monitoring YAMLs
- **Status:** NOT DONE
- **Credentials:** Need email server for AlertManager
- **Deliverable:** `deploy_monitoring_stack.yml` playbook

**Components to deploy (YAMLs exist in k8s-yamls-master):**
- Prometheus Operator + Server (60+ files)
- Grafana + 14 custom dashboards
- AlertManager with email notifications
- Node Exporter DaemonSet
- Kube State Metrics
- ServiceMonitors for Calico, CoreDNS, etcd, NGINX

**Per-cluster customization needed:**
- Ingress URLs
- Cluster name ConfigMaps
- etcd certificate secrets
- Prometheus scrape configs

---

### Task 6: Logging Stack Deployment
- **What:** Automate deployment of EXISTING Fluentd YAMLs
- **Status:** NOT DONE
- **Credentials:** neede for Splunk HEC tokens
- **Deliverable:** `deploy_logging_stack.yml` playbook

**Components to deploy:**
- Fluentd namespace + RBAC
- Fluentd ConfigMap with parsing rules
- Fluentd DaemonSet
- Splunk HEC integration
- Per-cluster ConfigMaps

---

### Task 7: Dashboard Deployment 
- **What:** Automate deployment of Kubernetes Dashboard YAMLs
- **Status:** NOT DONE
- **Credentials:** None needed
- **Deliverable:** `deploy_dashboard.yml` playbook

**Components:**
- Dashboard from `live/All-Clusters-BASE-REQUIRED/dashboard/recommended.yaml`
- Per-cluster ingress from `dashboard/{cluster}/3-ingress.yaml`

---

### Task 8: Metrics Server Deployment
- **What:** Automate Metrics Server deployment
- **Status:** NOT DONE
- **Credentials:** None needed
- **Deliverable:** `deploy_metrics_server.yml` playbook
- **File:** `live/All-Clusters-BASE-REQUIRED/metrics-server/0.7.2/high-availability-1.21+.yaml`

---

### Task 9: Disk Management Scripts
- Convert `e1-dbdisksetup.sh` and `resize-appdisk.sh`

---

### Task 10: Local Repository Configuration 
- Convert `mirepo.sh`


---


## Notes

- **Credentials:** Needed for AD, DSM, and Splunk. Credentials via environment variables or vars file
- **YAML Files:** All monitoring/logging YAMLs already exist in k8s-yamls-master - we're just automating deployment