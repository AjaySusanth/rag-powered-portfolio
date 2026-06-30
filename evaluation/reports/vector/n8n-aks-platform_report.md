# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 73.3%
- **Recall@5:** 60.0%
- **Mean Reciprocal Rank (MRR):** 0.569
- **Average Similarity (Hits):** 0.630
- **Unique Sources@5:** 4.20

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 70.0% | 0.467 | 0.606 |
| Data Models | 3 | 66.7% | 66.7% | 0.667 | 0.668 |
| Documentation | 2 | 100.0% | 75.0% | 1.000 | 0.618 |
| Infrastructure | 2 | 100.0% | 75.0% | 0.600 | 0.624 |
| Pipeline | 3 | 33.3% | 16.7% | 0.333 | 0.681 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 71.4% | 64.3% | 0.362 | 0.602 |
| Artifact | 11 | 54.5% | 50.0% | 0.545 | 0.653 |

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
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.538)
- **Failure Reason:** No expected sources retrieved.

### N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/secretproviderclass.yaml`
  - `helm/n8n/templates/main.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 0.699)
  - `docs/verification_ledger.md` (Similarity: 0.614)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 0.598)
  - `n8n-aks-platform/challenges.md` (Similarity: 0.598)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.577)
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
  - `helm/n8n/Chart.yaml` (Similarity: 0.463)
  - `n8n-aks-platform/decisions.md` (Similarity: 0.448)
  - `docs/verification_ledger.md` (Similarity: 0.443)
  - `docs/architecture/component-communication.md` (Similarity: 0.442)
  - `n8n-aks-platform/architecture.md` (Similarity: 0.433)
- **Failure Reason:** No expected sources retrieved.
