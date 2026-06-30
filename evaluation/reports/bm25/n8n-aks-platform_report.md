# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 73.3%
- **Recall@5:** 63.3%
- **Mean Reciprocal Rank (MRR):** 0.358
- **Average Similarity (Hits):** 37.247
- **Unique Sources@5:** 4.20

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 80.0% | 0.433 | 39.591 |
| Data Models | 3 | 66.7% | 66.7% | 0.500 | 31.546 |
| Documentation | 2 | 100.0% | 75.0% | 0.500 | 39.078 |
| Infrastructure | 2 | 50.0% | 50.0% | 0.100 | 30.800 |
| Pipeline | 3 | 66.7% | 33.3% | 0.167 | 39.654 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 71.4% | 71.4% | 0.345 | 38.592 |
| Artifact | 11 | 54.5% | 50.0% | 0.268 | 36.127 |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 34.191)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 29.958)
  - `n8n-aks-platform/decisions.md` (Similarity: 29.462)
  - `.github/workflows/ci.yaml` (Similarity: 25.550)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 23.773)
- **Failure Reason:** No expected sources retrieved.

### N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/secretproviderclass.yaml`
  - `helm/n8n/templates/main.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 50.648)
  - `docs/verification_ledger.md` (Similarity: 48.109)
  - `n8n-aks-platform/challenges.md` (Similarity: 34.212)
  - `n8n-aks-platform/architecture.md` (Similarity: 34.163)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 33.535)
- **Failure Reason:** No expected sources retrieved.

### N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Category:** Data Models
- **Expected Sources:**
  - `helm/n8n/values.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 27.245)
  - `n8n-aks-platform/architecture.md` (Similarity: 26.134)
  - `n8n-aks-platform/architecture.md` (Similarity: 25.218)
  - `docs/verification_ledger.md` (Similarity: 22.332)
  - `n8n-aks-platform/challenges.md` (Similarity: 21.956)
- **Failure Reason:** No expected sources retrieved.

### N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Category:** Infrastructure
- **Expected Sources:**
  - `terraform/env/dev/main.tf`
  - `terraform/modules/keyvault/main.tf`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 40.170)
  - `n8n-aks-platform/decisions.md` (Similarity: 39.121)
  - `terraform/modules/aks/outputs.tf` (Similarity: 38.201)
  - `n8n-aks-platform/challenges.md` (Similarity: 34.040)
  - `terraform/modules/aks/main.tf` (Similarity: 32.913)
- **Failure Reason:** No expected sources retrieved.
