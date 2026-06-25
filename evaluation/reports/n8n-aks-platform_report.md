# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 86.7%
- **Recall@5:** 70.0%
- **Mean Reciprocal Rank (MRR):** 0.574
- **Average Similarity (Hits):** 0.620

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 70.0% | 0.467 | 0.606 |
| Data Models | 3 | 66.7% | 66.7% | 0.667 | 0.668 |
| Documentation | 2 | 100.0% | 100.0% | 1.000 | 0.618 |
| Infrastructure | 2 | 100.0% | 75.0% | 0.600 | 0.624 |
| Pipeline | 3 | 100.0% | 50.0% | 0.361 | 0.605 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 100.0% | 92.9% | 0.438 | 0.581 |
| Artifact | 11 | 63.6% | 54.5% | 0.523 | 0.638 |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `docs/verification_ledger.md` (Similarity: 0.581)
  - `README.md` (Similarity: 0.544)
  - `README.md` (Similarity: 0.538)
  - `README.md` (Similarity: 0.532)
  - `helm/n8n/templates/webhook.yaml` (Similarity: 0.529)
- **Failure Reason:** No expected sources retrieved.

### N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Category:** Data Models
- **Expected Sources:**
  - `helm/n8n/values.yaml`
- **Retrieved Sources (Top-K):**
  - `README.md` (Similarity: 0.555)
  - `README.md` (Similarity: 0.467)
  - `helm/n8n/Chart.yaml` (Similarity: 0.464)
  - `README.md` (Similarity: 0.450)
  - `docs/verification_ledger.md` (Similarity: 0.443)
- **Failure Reason:** No expected sources retrieved.
