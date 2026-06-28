# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 66.7%
- **Recall@5:** 56.7%
- **Mean Reciprocal Rank (MRR):** 0.522
- **Average Similarity (Hits):** 0.634

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 70.0% | 0.467 | 0.606 |
| Data Models | 3 | 66.7% | 66.7% | 0.667 | 0.668 |
| Documentation | 2 | 100.0% | 75.0% | 1.000 | 0.618 |
| Infrastructure | 2 | 50.0% | 50.0% | 0.500 | 0.661 |
| Pipeline | 3 | 33.3% | 16.7% | 0.167 | 0.681 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 57.1% | 50.0% | 0.333 | 0.606 |
| Artifact | 11 | 54.5% | 50.0% | 0.500 | 0.653 |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 0.668)
  - `docs/verification_ledger.md` (Similarity: 0.581)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.561)
  - `README.md` (Similarity: 0.544)
  - `README.md` (Similarity: 0.539)
- **Failure Reason:** No expected sources retrieved.

### N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/secretproviderclass.yaml`
  - `helm/n8n/templates/main.yaml`
- **Retrieved Sources (Top-K):**
  - `README.md` (Similarity: 0.708)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.699)
  - `docs/verification_ledger.md` (Similarity: 0.614)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.598)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.598)
- **Failure Reason:** No expected sources retrieved.

### N8N-008
- **Question:** How does the KEDA autoscaling loop coordinate with the Redis message broker and the n8n-worker deployment to dynamically manage worker replica counts?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/hpa-worker.yaml`
  - `helm/n8n/templates/worker.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 0.753)
  - `README.md` (Similarity: 0.715)
  - `docs/verification_ledger.md` (Similarity: 0.707)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.667)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.643)
- **Failure Reason:** No expected sources retrieved.

### N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Category:** Data Models
- **Expected Sources:**
  - `helm/n8n/values.yaml`
- **Retrieved Sources (Top-K):**
  - `README.md` (Similarity: 0.555)
  - `README.md` (Similarity: 0.467)
  - `helm/n8n/Chart.yaml` (Similarity: 0.463)
  - `README.md` (Similarity: 0.450)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.448)
- **Failure Reason:** No expected sources retrieved.

### N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Category:** Infrastructure
- **Expected Sources:**
  - `terraform/env/dev/main.tf`
  - `terraform/modules/keyvault/main.tf`
- **Retrieved Sources (Top-K):**
  - `docs/verification_ledger.md` (Similarity: 0.684)
  - `docs/verification_ledger.md` (Similarity: 0.671)
  - `README.md` (Similarity: 0.643)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.620)
  - `README.md` (Similarity: 0.608)
- **Failure Reason:** No expected sources retrieved.
