# Retrieval Evaluation Report: n8n-aks-platform
- **Date Generated:** 2026-06-25T16:33:02Z
- **Top-K Configured:** 5
- **Total Questions:** 15

## Global Metrics
- **Hit Rate@5:** 73.3%
- **Recall@5:** 63.3%
- **Mean Reciprocal Rank (MRR):** 0.361
- **Average Similarity (Hits):** 36.989

## Category Metrics
| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Core Logic | 5 | 80.0% | 80.0% | 0.433 | 39.403 |
| Data Models | 3 | 66.7% | 66.7% | 0.500 | 31.295 |
| Documentation | 2 | 100.0% | 75.0% | 0.500 | 38.915 |
| Infrastructure | 2 | 50.0% | 50.0% | 0.125 | 30.528 |
| Pipeline | 3 | 66.7% | 33.3% | 0.167 | 39.159 |

## Layer Metrics
| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |
| --- | --- | --- | --- | --- | --- |
| Design | 7 | 71.4% | 71.4% | 0.345 | 38.366 |
| Artifact | 11 | 54.5% | 50.0% | 0.273 | 35.841 |

## Failure Analysis
### N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Category:** Core Logic
- **Expected Sources:**
  - `helm/n8n/templates/main.yaml`
  - `helm/n8n/templates/serviceaccounts.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 33.731)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 29.576)
  - `n8n-aks-platform/decisions.md` (Similarity: 28.978)
  - `.github/workflows/ci.yaml` (Similarity: 25.214)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 23.597)
- **Failure Reason:** No expected sources retrieved.

### N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Category:** Pipeline
- **Expected Sources:**
  - `helm/n8n/templates/secretproviderclass.yaml`
  - `helm/n8n/templates/main.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/decisions.md` (Similarity: 49.979)
  - `docs/verification_ledger.md` (Similarity: 47.620)
  - `n8n-aks-platform/challenges.md` (Similarity: 33.916)
  - `n8n-aks-platform/architecture.md` (Similarity: 33.857)
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 33.092)
- **Failure Reason:** No expected sources retrieved.

### N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Category:** Data Models
- **Expected Sources:**
  - `helm/n8n/values.yaml`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/lessons-learned.md` (Similarity: 26.955)
  - `n8n-aks-platform/architecture.md` (Similarity: 25.850)
  - `n8n-aks-platform/architecture.md` (Similarity: 24.895)
  - `docs/verification_ledger.md` (Similarity: 22.149)
  - `n8n-aks-platform/challenges.md` (Similarity: 21.641)
- **Failure Reason:** No expected sources retrieved.

### N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Category:** Infrastructure
- **Expected Sources:**
  - `terraform/env/dev/main.tf`
  - `terraform/modules/keyvault/main.tf`
- **Retrieved Sources (Top-K):**
  - `n8n-aks-platform/architecture.md` (Similarity: 39.313)
  - `n8n-aks-platform/decisions.md` (Similarity: 38.766)
  - `terraform/modules/aks/outputs.tf` (Similarity: 38.137)
  - `n8n-aks-platform/challenges.md` (Similarity: 33.357)
  - `terraform/modules/aks/main.tf` (Similarity: 32.703)
- **Failure Reason:** No expected sources retrieved.

## Comparison with Vector Baseline

| Metric | Vector Baseline | BM25 Retriever | Difference |
| --- | --- | --- | --- |
| **Hit Rate@5** | 86.7% | 73.3% | -13.4% |
| **Recall@5** | 70.0% | 63.3% | -6.7% |
| **MRR** | 0.574 | 0.361 | -0.213 |

### Analysis

- **Where BM25 Outperforms / is Crucial**:
  BM25 is highly effective for exact keyword matches, especially on code-heavy questions referencing specific Helm templates, configuration values, or exact function/identifier names (e.g. `verifyJWT`, `authMiddleware`, `SecretProviderClass`). In these instances, vector embeddings sometimes drift due to the high density of technical keywords, retrieving unrelated overview documents (`README.md` or general architecture files) instead of the exact configuration file. 
  
- **Where Vector Baseline Performs Better**:
  Vector retrieval performs significantly better on conceptual, natural language queries (e.g., questions asking about "how n8n pods securely retrieve database passwords" or "AKS identity permissions configuration"). BM25 fails here if the user query does not share exact vocabulary overlap with the source code chunks (e.g. searching "securely retrieve" when the code contains "TriggerAuthentication" or "SecretProviderClass" without the word "securely"). This is why Vector achieves a higher overall MRR (0.574 vs 0.361) and higher Hit Rate (86.7% vs 73.3%).
  
- **Conclusion**:
  This highlights the necessity of **Reciprocal Rank Fusion (RRF)** to combine the semantic understanding of Vector search with the exact keyword precision of BM25.
