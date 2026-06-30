# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 66.7%
- **Recall@5:** 60.0%
- **Mean Reciprocal Rank (MRR):** 0.467
- **Average Similarity (Hits):** 0.032
- **Unique Sources@5:** 5.00

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 80.0% | 0.400 | 0.032 |
| Data Models | 3 | 66.7% | 66.7% | 0.667 | 0.033 |
| Documentation | 2 | 100.0% | 75.0% | 0.750 | 0.032 |
| Infrastructure | 2 | 50.0% | 50.0% | 0.500 | 0.032 |
| Pipeline | 3 | 33.3% | 16.7% | 0.167 | 0.031 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 57.1% | 57.1% | 0.286 | 0.032 |
| Artifact | 11 | 54.5% | 50.0% | 0.455 | 0.032 |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 0.033)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.032)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.032)
  - `docs/verification_ledger.md` (Similarity: 0.030)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.028)
- **Failure Reason:** No expected sources retrieved.

### N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/secretproviderclass.yaml`
  - `helm/n8n/templates/main.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 0.033)
  - `docs/verification_ledger.md` (Similarity: 0.032)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.031)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.030)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.029)
- **Failure Reason:** No expected sources retrieved.

### N8N-008
- **Question:** How does the KEDA autoscaling loop coordinate with the Redis message broker and the n8n-worker deployment to dynamically manage worker replica counts?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/hpa-worker.yaml`
  - `helm/n8n/templates/worker.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 0.033)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.032)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.031)
  - `README.md` (Similarity: 0.031)
  - `docs/verification_ledger.md` (Similarity: 0.031)
- **Failure Reason:** No expected sources retrieved.

### N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Category:** Data Models
- **Expected Sources:**
  - `helm/n8n/values.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 0.030)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.029)
  - `docs/verification_ledger.md` (Similarity: 0.029)
  - `.github/workflows/ci.yaml` (Similarity: 0.028)
  - `helm/n8n/Chart.yaml` (Similarity: 0.016)
- **Failure Reason:** No expected sources retrieved.

### N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Category:** Infrastructure
- **Expected Sources:**
  - `terraform/env/dev/main.tf`
  - `terraform/modules/keyvault/main.tf`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 0.032)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.032)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.031)
  - `docs/verification_ledger.md` (Similarity: 0.031)
  - `terraform/modules/aks/outputs.tf` (Similarity: 0.030)
- **Failure Reason:** No expected sources retrieved.
