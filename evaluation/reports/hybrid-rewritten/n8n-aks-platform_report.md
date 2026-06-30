# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 86.7%
- **Recall@5:** 76.7%
- **Mean Reciprocal Rank (MRR):** 0.594
- **Average Similarity (Hits):** 0.032
- **Unique Sources@5:** 5.00

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 80.0% | 0.567 | 0.032 |
| Data Models | 3 | 100.0% | 100.0% | 0.750 | 0.031 |
| Documentation | 2 | 100.0% | 100.0% | 0.750 | 0.032 |
| Infrastructure | 2 | 50.0% | 50.0% | 0.500 | 0.033 |
| Pipeline | 3 | 100.0% | 50.0% | 0.444 | 0.032 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 85.7% | 85.7% | 0.481 | 0.031 |
| Artifact | 11 | 72.7% | 63.6% | 0.523 | 0.032 |

## Query Rewriter Analysis
- **Rewrite Rate:** 100.0% (15 / 15 queries)
- **Average Rewrite Latency:** 1179.5 ms

### Detailed Rewrite Decisions
| Question ID | Original Query | Rewritten Query | Rewritten? | Explanation | Latency |
| --- | --- | --- | :---: | --- | :---: |
| N8N-001 | How does the OPA Gatekeeper constraint template evaluate and prevent pods from running without specified container image tags or with the 'latest' tag in the dev namespace? | n8n-aks-platform OPA Gatekeeper ConstraintTemplate policy for container image tag validation, prevent 'latest' tag or missing tags in dev namespace | Yes | Expanded the query to include the specific project context and technical keywords like 'ConstraintTemplate' and 'policy' to ensure the retrieval system targets the OPA policy definitions and Rego logic within the n8n-aks-platform repository. | 1957.4 ms |
| N8N-002 | How does the OPA Gatekeeper policy ensure that every container and initContainer in a pod defines CPU and Memory requests and limits prior to scheduler placement? | OPA Gatekeeper constraint template for Kubernetes Pod CPU and Memory resource requests and limits validation in n8n-aks-platform | Yes | The original query was conversational. I expanded it to include specific technical terms like 'constraint template' and 'resource requests and limits validation' to better target the OPA Gatekeeper policy definitions within the n8n-aks-platform context. | 1086.1 ms |
| N8N-003 | How does the NetworkPolicy configuration isolate inter-pod communication for the database layer (Postgres and Redis) while allowing necessary metrics collection and operator polling? | n8n-aks-platform Kubernetes NetworkPolicy configuration for Postgres and Redis database layer isolation, allowing metrics collection and operator polling traffic | Yes | Expanded the query to include the project context and specific technical requirements (NetworkPolicy, database isolation, metrics, and operator polling) to ensure the retrieval system targets the relevant Kubernetes manifests and security policies. | 1095.9 ms |
| N8N-004 | Why and how does the n8n egress NetworkPolicy permit outbound traffic to the public internet while strictly blocking lateral access to internal private IP ranges? | n8n-aks-platform Kubernetes NetworkPolicy egress configuration public internet access vs internal private IP range restriction | Yes | Expanded the query to include specific technical context (Kubernetes NetworkPolicy, egress configuration) to ensure the retrieval system focuses on the relevant infrastructure-as-code files and security policies within the n8n-aks-platform project. | 1042.7 ms |
| N8N-005 | How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards? | n8n-aks-platform Helm chart securityContext podSecurityContext allowPrivilegeEscalation readOnlyRootFilesystem runAsNonRoot zero-trust configuration | Yes | Expanded the query to include specific Kubernetes security fields (securityContext, allowPrivilegeEscalation, etc.) relevant to zero-trust standards within the n8n-aks-platform Helm chart context to improve retrieval precision. | 1244.9 ms |
| N8N-006 | How does the Helm Chart CI pipeline automate chart version promotion and synchronize state changes with ArgoCD upon a git commit to the Helm directory? | n8n-aks-platform Helm Chart CI pipeline automation chart version promotion ArgoCD synchronization git commit workflow | Yes | Expanded the query to include the project context and key technical terms to ensure the retrieval system focuses on the specific CI/CD integration between Helm, Git, and ArgoCD within the n8n-aks-platform repository. | 1120.2 ms |
| N8N-007 | How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests? | n8n-aks-platform Azure Key Vault integration SecretProviderClass CSI driver pod identity managed identity database password encryption key retrieval | Yes | Expanded the query to include specific Kubernetes and Azure integration technologies (CSI driver, SecretProviderClass, managed identity) relevant to the n8n-aks-platform context to ensure retrieval of documentation regarding secure secret injection. | 1107.3 ms |
| N8N-008 | How does the KEDA autoscaling loop coordinate with the Redis message broker and the n8n-worker deployment to dynamically manage worker replica counts? | KEDA ScaledObject Redis trigger configuration n8n-worker deployment autoscaling mechanism architecture | Yes | Expanded the query to include specific KEDA components like ScaledObject and Redis triggers to ensure the retrieval system focuses on the technical implementation of the autoscaling loop within the n8n-aks-platform context. | 1377.3 ms |
| N8N-009 | How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema? | n8n-aks-platform Helm values.yaml resource requests and limits configuration for n8n components and database instances | Yes | Expanded the query to include specific configuration file references (values.yaml) and project context to ensure the retrieval system targets the Helm chart definitions for resource management. | 1207.7 ms |
| N8N-010 | How are Azure Key Vault secret objects mapped to specific environment variable keys inside the SecretProviderClass definition? | n8n-aks-platform SecretProviderClass Azure Key Vault secret object mapping to environment variables configuration syntax | Yes | Expanded the query to include the project context and specific technical keywords related to the Secret Store CSI driver configuration to improve retrieval of relevant YAML definitions. | 1231.9 ms |
| N8N-011 | How is the PrometheusRule alerting expression for high workflow failure rates calculated using metrics from n8n queue execution? | n8n-aks-platform PrometheusRule alerting expression high workflow failure rate calculation n8n queue execution metrics | Yes | The query was expanded to include the project context and specific technical keywords to ensure the retrieval system focuses on Prometheus alerting rules and n8n queue metrics within the AKS platform context. | 933.1 ms |
| N8N-012 | How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets? | AKS Terraform configuration for kubelet identity user-assigned vs system-assigned managed identity Azure Key Vault secret provider class access | Yes | Expanded the query to include specific technical keywords like 'managed identity', 'secret provider class', and 'AKS Terraform configuration' to ensure retrieval of relevant infrastructure-as-code documentation and examples. | 1218.6 ms |
| N8N-013 | How is the Azure federated identity credential structured in Terraform to authenticate GitHub Actions CI/CD workflows using OIDC rather than static secrets? | Terraform azurerm_federated_identity_credential configuration for GitHub Actions OIDC authentication in n8n-aks-platform | Yes | Expanded the query to include the specific Terraform resource type (azurerm_federated_identity_credential) and the context of OIDC authentication to ensure retrieval of relevant infrastructure-as-code documentation. | 1106.0 ms |
| N8N-014 | Which inter-service paths are explicitly blocked by the NetworkPolicy architecture, and what architectural reasons justify preventing workers from communicating directly with the main API or webhooks? | n8n-aks-platform NetworkPolicy inter-service communication restrictions, architectural justification for blocking worker to API and webhook direct traffic | Yes | The query was expanded to include the project context and specific technical terms to ensure the retrieval system focuses on the Kubernetes NetworkPolicy implementation and the security rationale for the n8n architecture. | 1016.3 ms |
| N8N-015 | How was compliance with named ServiceAccounts and resource limits verified across all running n8n pods in the cluster, as documented in the verification ledger? | n8n-aks-platform verification ledger compliance ServiceAccount resource limits pods | Yes | The query was rewritten to prioritize key technical terms and project context, removing conversational filler to improve vector search relevance for the verification ledger documentation. | 946.6 ms |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 0.033)
  - `docs/verification_ledger.md` (Similarity: 0.033)
  - `helm/n8n/templates/webhook.yaml` (Similarity: 0.031)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.030)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.029)
- **Failure Reason:** No expected sources retrieved.

### N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Category:** Infrastructure
- **Expected Sources:**
  - `terraform/env/dev/main.tf`
  - `terraform/modules/keyvault/main.tf`
- **Retrieved Sources (Top-K):**
  - `docs/verification_ledger.md` (Similarity: 0.032)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.031)
  - `terraform/modules/aks/outputs.tf` (Similarity: 0.031)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.031)
  - `helm/n8n/templates/secretproviderclass.yaml` (Similarity: 0.030)
- **Failure Reason:** No expected sources retrieved.
