# Retrieval Diagnostics Report: n8n-aks-platform
- **Total Queries:** 15
- **Failed Queries:** 5

## Summary of Diagnostic Metrics
- **Average Candidate Overlap Count (Top 20):** 12.80
- **Average Jaccard Overlap (Top 20):** 0.4872
- **Average Duplicate Chunk Density (Top 5):** 1.16 (chunks per unique source file)

## Failure Category Breakdown
| Failure Category | Count | Recommended Optimization |
| --- | :---: | --- |
| Missing from both retrievers | 1 | Improve retrieval quality, chunking, or indexing. |
| Candidate starvation | 6 | Increase retrieval candidate pool before fusion. |
| Fusion ordering | 2 | Tune RRF parameters or investigate fusion strategy. |
| Duplicate source domination | 0 | Implement Source Diversification. |

### Next Recommended Step
**Larger candidate pool (increase retrieval candidate pool size before fusion).**

## Detailed Failure Analysis
### Query N8N-005
- **Question:** How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?
- **Top-5 Fused Sources:** n8n-aks-platform/architecture.md, n8n-aks-platform/decisions.md, n8n-aks-platform/lessons-learned.md, docs/verification_ledger.md, n8n-aks-platform/lessons-learned.md
- **Unretrieved Expected Sources Analysis:**
  - **Source File:** `helm/n8n/templates/main.yaml`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** 15
    - **BM25 Rank (Top 20):** Not present
    - **RRF Fused Rank (Top 20):** 22
    - **Explanation:** The expected file was retrieved (fused rank: 22) but both Vector rank (15) and BM25 rank (None) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.
  - **Source File:** `helm/n8n/templates/serviceaccounts.yaml`
    - **Failure Category:** Missing from both retrievers
    - **Vector Rank (Top 20):** Not present
    - **BM25 Rank (Top 20):** Not present
    - **RRF Fused Rank (Top 20):** Not present
    - **Explanation:** The expected file 'helm/n8n/templates/serviceaccounts.yaml' did not appear in the top-20 candidates of either Vector or BM25 search.
    - **Engineering Recommendation:** Improve retrieval quality, chunking, or indexing.

### Query N8N-007
- **Question:** How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?
- **Top-5 Fused Sources:** n8n-aks-platform/decisions.md, docs/verification_ledger.md, n8n-aks-platform/lessons-learned.md, n8n-aks-platform/challenges.md, n8n-aks-platform/architecture.md
- **Unretrieved Expected Sources Analysis:**
  - **Source File:** `helm/n8n/templates/secretproviderclass.yaml`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** 6
    - **BM25 Rank (Top 20):** Not present
    - **RRF Fused Rank (Top 20):** 12
    - **Explanation:** The expected file was retrieved (fused rank: 12) but both Vector rank (6) and BM25 rank (None) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.
  - **Source File:** `helm/n8n/templates/main.yaml`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** Not present
    - **BM25 Rank (Top 20):** 6
    - **RRF Fused Rank (Top 20):** 13
    - **Explanation:** The expected file was retrieved (fused rank: 13) but both Vector rank (None) and BM25 rank (6) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.

### Query N8N-008
- **Question:** How does the KEDA autoscaling loop coordinate with the Redis message broker and the n8n-worker deployment to dynamically manage worker replica counts?
- **Top-5 Fused Sources:** n8n-aks-platform/architecture.md, n8n-aks-platform/challenges.md, n8n-aks-platform/decisions.md, README.md, docs/verification_ledger.md
- **Unretrieved Expected Sources Analysis:**
  - **Source File:** `helm/n8n/templates/hpa-worker.yaml`
    - **Failure Category:** Fusion ordering
    - **Vector Rank (Top 20):** 8
    - **BM25 Rank (Top 20):** 4
    - **RRF Fused Rank (Top 20):** 6
    - **Explanation:** The expected file entered the RRF pool but was ranked poorly (fused rank: 6, deduplicated rank: 6) due to weak scores in both retrievers.
    - **Engineering Recommendation:** Tune RRF parameters or investigate fusion strategy.
  - **Source File:** `helm/n8n/templates/worker.yaml`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** Not present
    - **BM25 Rank (Top 20):** 11
    - **RRF Fused Rank (Top 20):** 14
    - **Explanation:** The expected file was retrieved (fused rank: 14) but both Vector rank (None) and BM25 rank (11) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.

### Query N8N-009
- **Question:** How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?
- **Top-5 Fused Sources:** n8n-aks-platform/decisions.md, n8n-aks-platform/architecture.md, docs/verification_ledger.md, .github/workflows/ci.yaml, helm/n8n/Chart.yaml
- **Unretrieved Expected Sources Analysis:**
  - **Source File:** `helm/n8n/values.yaml`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** 6
    - **BM25 Rank (Top 20):** Not present
    - **RRF Fused Rank (Top 20):** 12
    - **Explanation:** The expected file was retrieved (fused rank: 12) but both Vector rank (6) and BM25 rank (None) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.

### Query N8N-012
- **Question:** How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?
- **Top-5 Fused Sources:** n8n-aks-platform/decisions.md, n8n-aks-platform/architecture.md, n8n-aks-platform/challenges.md, docs/verification_ledger.md, docs/verification_ledger.md
- **Unretrieved Expected Sources Analysis:**
  - **Source File:** `terraform/env/dev/main.tf`
    - **Failure Category:** Candidate starvation
    - **Vector Rank (Top 20):** 19
    - **BM25 Rank (Top 20):** 18
    - **RRF Fused Rank (Top 20):** 16
    - **Explanation:** The expected file was retrieved (fused rank: 16) but both Vector rank (19) and BM25 rank (18) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.
    - **Engineering Recommendation:** Increase retrieval candidate pool before fusion.
  - **Source File:** `terraform/modules/keyvault/main.tf`
    - **Failure Category:** Fusion ordering
    - **Vector Rank (Top 20):** 5
    - **BM25 Rank (Top 20):** 19
    - **RRF Fused Rank (Top 20):** 10
    - **Explanation:** The expected file entered the RRF pool but was ranked poorly (fused rank: 10, deduplicated rank: 8) due to weak scores in both retrievers.
    - **Engineering Recommendation:** Tune RRF parameters or investigate fusion strategy.
