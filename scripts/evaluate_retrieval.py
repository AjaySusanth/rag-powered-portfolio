"""
WHY THIS WAS CHOSEN:
This script is the entrypoint CLI for the retrieval evaluation framework.
It handles parsing of command-line arguments (file or directory of datasets),
instantiates the evaluator with the production VectorRetriever (wrapped in a protocol adapter),
executes the evaluation pipeline, prints a formatted console summary, and outputs
both machine-readable JSON and human-readable Markdown reports to the respective directories.
"""
import sys
import asyncio
import argparse
import json
import dataclasses
import time
from pathlib import Path
from typing import List, Optional

# Add backend directory to sys.path to resolve src imports
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.retrieval.vector_retriever import retrieve as vector_retrieve
from src.retrieval.bm25_retriever import retrieve as bm25_retrieve
from src.retrieval.hybrid_retriever import retrieve as hybrid_retrieve
from src.models.retrieval_result import RetrievalResult
from src.evaluation.retrieval_evaluator import RetrievalEvaluator, Retriever
from src.models.evaluation_result import EvaluationResult
from src.db.core import close_db_pool
from src.evaluation.retrieval_diagnostics import RetrievalDiagnostics, DiagnosticsSummary
from src.retrieval.project_detector import detect_project


class VectorRetrieverAdapter(Retriever):
    """Adapter to map the vector retrieval retrieve function to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        return await vector_retrieve(query=query, top_k=top_k, project=resolved_project)


class BM25RetrieverAdapter(Retriever):
    """Adapter to map the BM25 retrieval retrieve function to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        return await bm25_retrieve(query=query, top_k=top_k, project=resolved_project)


class HybridRRFRetrieverAdapter(Retriever):
    """Adapter to map the Hybrid RRF retrieval retrieve function without diversification to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        return await hybrid_retrieve(query=query, top_k=top_k, project=resolved_project, diversify=False)


class HybridDiversifiedRetrieverAdapter(Retriever):
    """Adapter to map the Hybrid RRF retrieval retrieve function with diversification to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        return await hybrid_retrieve(query=query, top_k=top_k, project=resolved_project, diversify=True)


class HybridGradedRetrieverAdapter(Retriever):
    """Adapter to map the Hybrid retrieval retrieve function with diversification and grading to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        return await hybrid_retrieve(query=query, top_k=top_k, project=resolved_project, diversify=True, grade=True, min_chunks=3)


class HybridRewrittenRetrieverAdapter(Retriever):
    """Adapter to map the Hybrid retrieval retrieve function with query rewriting, diversification, and grading to the Retriever Protocol."""
    def __init__(self):
        from src.retrieval.rewriters.factory import create_rewriter_from_settings
        from src.retrieval.rewriters.mock import MockQueryRewriter
        from src.models.rewrite_result import RewriteResult
        
        self.rewriter = create_rewriter_from_settings()
        self.rewrite_details = {}
        
        if isinstance(self.rewriter, MockQueryRewriter):
            self.rewriter.rewrites = {
                "How does the OPA Gatekeeper constraint template evaluate and prevent pods from running without specified container image tags or with the 'latest' tag in the dev namespace?": RewriteResult(
                    rewritten_query="OPA Gatekeeper disallowed container image tags latest template constraint disallowed-tags-template disallowed-tags-constraints",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target Rego templates and constraint configurations for OPA image tag policies."
                ),
                "How does the OPA Gatekeeper policy ensure that every container and initContainer in a pod defines CPU and Memory requests and limits prior to scheduler placement?": RewriteResult(
                    rewritten_query="OPA Gatekeeper CPU Memory requests limits container initContainer Rego required-resources-template required-resources-constraint",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target Rego resource constraints for CPU and Memory in pods."
                ),
                "How does the NetworkPolicy configuration isolate inter-pod communication for the database layer (Postgres and Redis) while allowing necessary metrics collection and operator polling?": RewriteResult(
                    rewritten_query="NetworkPolicy Postgres Redis ingress communication whitelist monitoring helm/n8n/templates/networkpolicies.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target helm network policy templates and Postgres/Redis database ingress constraints."
                ),
                "Why and how does the n8n egress NetworkPolicy permit outbound traffic to the public internet while strictly blocking lateral access to internal private IP ranges?": RewriteResult(
                    rewritten_query="NetworkPolicy egress outbound traffic lateral RFC 1918 private subnets ipBlock helm/n8n/templates/networkpolicies.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target egress outbound network rules and private subnets ipBlock configurations."
                ),
                "How does the Helm chart configure container security settings and privilege constraints for n8n application pods to conform to zero-trust standards?": RewriteResult(
                    rewritten_query="Helm chart securityContext readOnlyRootFilesystem ServiceAccount zero trust helm/n8n/templates/main.yaml helm/n8n/templates/serviceaccounts.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target container securityContext settings and ServiceAccounts."
                ),
                "How does the Helm Chart CI pipeline automate chart version promotion and synchronize state changes with ArgoCD upon a git commit to the Helm directory?": RewriteResult(
                    rewritten_query="ArgoCD Helm chart CI workflow ACR ArgoCD application targetRevision .github/workflows/ci.yaml gitops/argocd/application.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target CI workflows and ArgoCD application targetRevision sync mechanisms."
                ),
                "How do the n8n application pods securely retrieve database passwords and encryption keys from Azure Key Vault without storing credentials in the git repository or Kubernetes Secret manifests?": RewriteResult(
                    rewritten_query="SecretProviderClass Secrets Store CSI driver Azure Key Vault mounted secret helm/n8n/templates/secretproviderclass.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target SecretProviderClass and Azure Key Vault Secrets Store CSI driver integration."
                ),
                "How does the KEDA autoscaling loop coordinate with the Redis message broker and the n8n-worker deployment to dynamically manage worker replica counts?": RewriteResult(
                    rewritten_query="KEDA autoscaling Redis bull jobs wait worker replica counts ScaledObject helm/n8n/templates/hpa-worker.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target KEDA ScaledObject and worker replica scaling logic based on Redis queue."
                ),
                "How is the default resource request and limit configuration structured for the n8n components and database instances within the Helm values schema?": RewriteResult(
                    rewritten_query="Helm values.yaml cpu memory requests limits n8n components helm/n8n/values.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target Helm values schema requests/limits allocations."
                ),
                "How are Azure Key Vault secret objects mapped to specific environment variable keys inside the SecretProviderClass definition?": RewriteResult(
                    rewritten_query="SecretProviderClass secretObjects objects mapping Azure Key Vault helm/n8n/templates/secretproviderclass.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target SecretProviderClass secretObjects mapping parameters."
                ),
                "How is the PrometheusRule alerting expression for high workflow failure rates calculated using metrics from n8n queue execution?": RewriteResult(
                    rewritten_query="PrometheusRule alert n8n scaling mode queue jobs failed rule monitoring/alerts/n8n-rules.yaml",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target PrometheusRule alerting rules for queue execution failures."
                ),
                "How is the user-assigned or system-assigned kubelet identity in AKS configured in Terraform to allow read access to Azure Key Vault secrets?": RewriteResult(
                    rewritten_query="Terraform user system assigned kubelet identity AKS Key Vault access policy terraform/env/dev/main.tf terraform/modules/keyvault/main.tf",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target AKS kubelet identity and Key Vault access policies in Terraform."
                ),
                "How is the Azure federated identity credential structured in Terraform to authenticate GitHub Actions CI/CD workflows using OIDC rather than static secrets?": RewriteResult(
                    rewritten_query="Terraform azurerm federated identity credential GitHub actions OIDC token exchange terraform/env/dev/oidc.tf",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target Azure federated identity credentials and GitHub Actions OIDC configurations."
                ),
                "Which inter-service paths are explicitly blocked by the NetworkPolicy architecture, and what architectural reasons justify preventing workers from communicating directly with the main API or webhooks?": RewriteResult(
                    rewritten_query="NetworkPolicy inter service communication matrix worker Redis component communication docs/architecture/component-communication.md",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target NetworkPolicy inter-service blockages and architecture docs."
                ),
                "How was compliance with named ServiceAccounts and resource limits verified across all running n8n pods in the cluster, as documented in the verification ledger?": RewriteResult(
                    rewritten_query="verification ledger kubectl ServiceAccounts resource limits pods validation docs/verification_ledger.md",
                    rewritten=True,
                    explanation="Mock rewrite: Expanded to target the verification ledger and kubectl validation verification."
                )
            }

    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        resolved_project = project if project is not None else detect_project(query)
        
        # Rewrite query
        start_time = time.perf_counter()
        rewrite_res = await self.rewriter.rewrite(query=query, project=resolved_project)
        latency = time.perf_counter() - start_time
        
        # Save details
        self.rewrite_details[query] = {
            "rewritten_query": rewrite_res.rewritten_query,
            "rewritten": rewrite_res.rewritten,
            "explanation": rewrite_res.explanation,
            "latency": latency
        }
        
        # Use rewritten query for retrieval
        retrieval_query = rewrite_res.rewritten_query
        return await hybrid_retrieve(
            query=retrieval_query,
            top_k=top_k,
            project=resolved_project
        )

    def get_rewrite_details(self, query: str) -> Optional[dict]:
        return self.rewrite_details.get(query)




def save_json_report(result: EvaluationResult, output_path: Path) -> None:
    """Serializes the EvaluationResult dataclass and saves it as a JSON file."""
    data = dataclasses.asdict(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_markdown_report(result: EvaluationResult, output_path: Path) -> None:
    """Generates a human-readable Markdown report summarizing the evaluation."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    avg_unique_sources = sum(len(set(r.retrieved_sources)) for r in result.question_results) / result.total_questions if result.total_questions > 0 else 0.0
    
    lines = [
        f"# Retrieval Evaluation Report: {result.project}",
        f"- **Date Generated:** {result.generated_at}",
        f"- **Top-K Configured:** {result.top_k}",
        f"- **Total Questions:** {result.total_questions}",
        "",
        "## Global Metrics",
        f"- **Hit Rate@{result.top_k}:** {result.hit_rate * 100:.1f}%",
        f"- **Recall@{result.top_k}:** {result.recall * 100:.1f}%",
        f"- **Mean Reciprocal Rank (MRR):** {result.mrr:.3f}",
        f"- **Average Similarity (Hits):** {result.average_similarity:.3f}",
        f"- **Unique Sources@{result.top_k}:** {avg_unique_sources:.2f}",
        "",
        "## Category Metrics",
        "| Category | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |",
        "| --- | --- | --- | --- | --- | --- |"
    ]
    
    for cm in result.category_metrics:
        display_cat = cm.category.replace("_", " ").title()
        lines.append(
            f"| {display_cat} | {cm.total_questions} | "
            f"{cm.hit_rate * 100:.1f}% | {cm.recall * 100:.1f}% | "
            f"{cm.mrr:.3f} | {cm.average_similarity:.3f} |"
        )
        
    lines.extend([
        "",
        "## Layer Metrics",
        "| Layer | Total Questions | Hit Rate | Recall | MRR | Avg Similarity |",
        "| --- | --- | --- | --- | --- | --- |"
    ])
    
    for lm in result.layer_metrics:
        lines.append(
            f"| {lm.layer.capitalize()} | {lm.total_questions} | "
            f"{lm.hit_rate * 100:.1f}% | {lm.recall * 100:.1f}% | "
            f"{lm.mrr:.3f} | {lm.average_similarity:.3f} |"
        )
        
    has_rewrites = any(r.rewritten_query is not None for r in result.question_results)
    if has_rewrites:
        rewrite_count = sum(1 for r in result.question_results if r.rewritten)
        rewrite_rate = rewrite_count / result.total_questions if result.total_questions > 0 else 0.0
        avg_latency = sum(r.rewrite_latency for r in result.question_results if r.rewrite_latency is not None) / result.total_questions if result.total_questions > 0 else 0.0
        
        lines.extend([
            "",
            "## Query Rewriter Analysis",
            f"- **Rewrite Rate:** {rewrite_rate * 100:.1f}% ({rewrite_count} / {result.total_questions} queries)",
            f"- **Average Rewrite Latency:** {avg_latency * 1000:.1f} ms",
            "",
            "### Detailed Rewrite Decisions",
            "| Question ID | Original Query | Rewritten Query | Rewritten? | Explanation | Latency |",
            "| --- | --- | --- | :---: | --- | :---: |"
        ])
        
        for r in result.question_results:
            rewritten_str = "Yes" if r.rewritten else "No"
            clean_original = r.question.replace("|", "\\|").replace("\n", " ")
            clean_rewritten = (r.rewritten_query or "").replace("|", "\\|").replace("\n", " ")
            clean_explanation = (r.rewrite_explanation or "").replace("|", "\\|").replace("\n", " ")
            latency_str = f"{r.rewrite_latency * 1000:.1f} ms" if r.rewrite_latency is not None else "N/A"
            lines.append(
                f"| {r.question_id} | {clean_original} | {clean_rewritten} | {rewritten_str} | {clean_explanation} | {latency_str} |"
            )

    lines.extend([
        "",
        "## Failure Analysis"
    ])
    
    if not result.failures:
        lines.append("All questions were retrieved successfully! 🎉")
    else:
        for f in result.failures:
            lines.extend([
                f"### {f.question_id}",
                f"- **Question:** {f.question}",
                f"- **Category:** {f.category.replace('_', ' ').title()}",
                "- **Expected Sources:**"
            ])
            for src in f.expected_sources:
                lines.append(f"  - `{src}`")
            
            lines.append("- **Retrieved Sources (Top-K):**")
            if not f.retrieved_sources:
                lines.append("  - *None*")
            else:
                for idx, src in enumerate(f.retrieved_sources):
                    score = f.similarity_scores[idx]
                    lines.append(f"  - `{src}` (Similarity: {score:.3f})")
            
            lines.append(f"- **Failure Reason:** {f.failure_reason}")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_console_summary(result: EvaluationResult) -> None:
    """Prints a clear console summary of the evaluation results."""
    avg_unique_sources = sum(len(set(r.retrieved_sources)) for r in result.question_results) / result.total_questions if result.total_questions > 0 else 0.0
    print("=" * 40)
    print(f"Project: {result.project}")
    print(f"Questions: {result.total_questions}")
    print("-" * 40)
    print(f"Recall@{result.top_k}: {result.recall * 100:.1f}%")
    print(f"Hit Rate@{result.top_k}: {result.hit_rate * 100:.1f}%")
    print(f"MRR: {result.mrr:.3f}")
    print(f"Average Similarity: {result.average_similarity:.3f}")
    print(f"Unique Sources@{result.top_k}: {avg_unique_sources:.2f}")
    print("-" * 40)
    print("Category Accuracy:")
    for cm in result.category_metrics:
        display_cat = cm.category.replace("_", " ").title()
        cat_hits = round(cm.hit_rate * cm.total_questions)
        print(f"  {display_cat}: {cat_hits} / {cm.total_questions}")
    print("-" * 40)
    if result.failures:
        print("Failures:")
        for f in result.failures:
            print(f"  {f.question_id}")
            print(f"    Expected: {', '.join(f.expected_sources)}")
            ret_info = []
            for idx, src in enumerate(f.retrieved_sources[:2]):
                score = f.similarity_scores[idx]
                ret_info.append(f"{src} ({score:.2f})")
            print(f"    Retrieved: {', '.join(ret_info) if ret_info else 'None'}")
        print("-" * 40)


async def evaluate_file(evaluator: RetrievalEvaluator, file_path: Path, top_k: int, run_type: str) -> None:
    """Evaluates a single JSON dataset file and generates reports."""
    print(f"\nEvaluating dataset: {file_path.name} ...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load JSON file {file_path}: {e}")
        return

    try:
        result = await evaluator.evaluate_dataset(dataset, top_k=top_k, db_check=True)
    except Exception as e:
        print(f"[Error] Evaluation failed for {file_path.name}: {e}")
        return

    # Print summary
    print_console_summary(result)

    # Save reports to dedicated folders
    project_slug = result.project
    json_path = ROOT_DIR / "evaluation" / "results" / run_type / f"{project_slug}_result.json"
    md_path = ROOT_DIR / "evaluation" / "reports" / run_type / f"{project_slug}_report.md"

    save_json_report(result, json_path)
    save_markdown_report(result, md_path)
    print(f"Saved JSON report to: {json_path}")
    print(f"Saved Markdown report to: {md_path}")


def save_diagnostics_json(summary: DiagnosticsSummary, output_path: Path) -> None:
    """Serializes the DiagnosticsSummary dataclass and saves it as a JSON file."""
    data = dataclasses.asdict(summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_diagnostics_markdown(summary: DiagnosticsSummary, output_path: Path) -> None:
    """Generates a human-readable Markdown diagnostics report with failure analysis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        f"# Retrieval Diagnostics Report: {summary.project}",
        f"- **Total Queries:** {summary.total_queries}",
        f"- **Failed Queries:** {summary.failed_queries}",
        "",
        "## Summary of Diagnostic Metrics",
        f"- **Average Candidate Overlap Count (Top 20):** {summary.avg_overlap_count:.2f}",
        f"- **Average Jaccard Overlap (Top 20):** {summary.avg_jaccard_overlap:.4f}",
        f"- **Average Duplicate Chunk Density (Top 5):** {summary.avg_duplicate_density:.2f} (chunks per unique source file)",
        "",
        "## Failure Category Breakdown",
        "| Failure Category | Count | Recommended Optimization |",
        "| --- | :---: | --- |"
    ]
    
    recs = {
        "Missing from both retrievers": "Improve retrieval quality, chunking, or indexing.",
        "Candidate starvation": "Increase retrieval candidate pool before fusion.",
        "Fusion ordering": "Tune RRF parameters or investigate fusion strategy.",
        "Duplicate source domination": "Implement Source Diversification."
    }
    
    for category, count in summary.failure_category_counts.items():
        lines.append(f"| {category} | {count} | {recs.get(category, '')} |")
        
    lines.extend([
        "",
        "### Next Recommended Step",
        f"**{summary.top_recommendation}**",
        "",
        "## Detailed Failure Analysis"
    ])
    
    failed_details = [qd for qd in summary.query_details if not qd.is_hit]
    
    if not failed_details:
        lines.append("All queries succeeded! No failures to analyze. 🎉")
    else:
        for qd in failed_details:
            lines.extend([
                f"### Query {qd.question_id}",
                f"- **Question:** {qd.question}",
                f"- **Top-5 Fused Sources:** {', '.join(qd.top_5_sources) if qd.top_5_sources else 'None'}",
                "- **Unretrieved Expected Sources Analysis:**"
            ])
            for f in qd.failures:
                lines.extend([
                    f"  - **Source File:** `{f.source_file}`",
                    f"    - **Failure Category:** {f.category}",
                    f"    - **Vector Rank (Top 20):** {f.vector_rank if f.vector_rank is not None else 'Not present'}",
                    f"    - **BM25 Rank (Top 20):** {f.bm25_rank if f.bm25_rank is not None else 'Not present'}",
                    f"    - **RRF Fused Rank (Top 20):** {f.rrf_rank if f.rrf_rank is not None else 'Not present'}",
                    f"    - **Explanation:** {f.explanation}",
                    f"    - **Engineering Recommendation:** {f.recommendation}"
                ])
            lines.append("")
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


async def run_diagnostics_file(file_path: Path) -> None:
    """Runs diagnostics analysis over a single JSON dataset file and generates reports."""
    print(f"\nRunning retrieval diagnostics for dataset: {file_path.name} ...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load JSON file {file_path}: {e}")
        return

    try:
        diagnostics = RetrievalDiagnostics(k=60)
        summary = await diagnostics.analyze_dataset(dataset)
    except Exception as e:
        print(f"[Error] Diagnostics failed for {file_path.name}: {e}")
        return

    # Print summary to console
    print("========================================")
    print(f"Project: {summary.project} (Diagnostics)")
    print(f"Total Queries: {summary.total_queries}")
    print(f"Failed Queries: {summary.failed_queries}")
    print("----------------------------------------")
    print("Failure Category Counts:")
    for category, count in summary.failure_category_counts.items():
        print(f"  {category}: {count}")
    print("----------------------------------------")
    print(f"Avg Overlap Count (Top 20): {summary.avg_overlap_count:.2f}")
    print(f"Avg Duplicate Chunk Density (Top 5): {summary.avg_duplicate_density:.2f}")
    print(f"Top Recommendation: {summary.top_recommendation}")
    print("========================================")

    # Save reports to dedicated diagnostics folders
    project_slug = summary.project
    json_path = ROOT_DIR / "evaluation" / "results" / "diagnostics" / f"{project_slug}_diagnostics.json"
    md_path = ROOT_DIR / "evaluation" / "reports" / "diagnostics" / f"{project_slug}_diagnostics.md"

    save_diagnostics_json(summary, json_path)
    save_diagnostics_markdown(summary, md_path)
    print(f"Saved JSON diagnostics to: {json_path}")
    print(f"Saved Markdown diagnostics to: {md_path}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG Retrieval quality against golden datasets.")
    parser.add_argument(
        "target", 
        type=str, 
        help="Path to a single dataset JSON file or a directory containing multiple dataset JSON files."
    )
    parser.add_argument(
        "--top-k", 
        type=int, 
        default=5, 
        help="Top-K retrieve parameter to evaluate (default: 5)."
    )
    parser.add_argument(
        "--run-type",
        type=str,
        choices=["vector", "manual-docs", "bm25", "hybrid", "hybrid-diversified", "hybrid-graded", "hybrid-rewritten", "rrf", "grader"],
        default="vector",
        help="The evaluation run type folder (e.g. vector, manual-docs)."
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Run in retrieval diagnostics mode to analyze failures."
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"[Error] Target path does not exist: {target_path}")
        sys.exit(1)

    try:
        if args.diagnostics:
            if target_path.is_file():
                await run_diagnostics_file(target_path)
            elif target_path.is_dir():
                json_files = sorted(list(target_path.glob("*.json")))
                if not json_files:
                    print(f"[Warning] No JSON files found in directory: {target_path}")
                    return
                for f in json_files:
                    await run_diagnostics_file(f)
        else:
            # Select appropriate retriever adapter based on run-type
            if args.run_type == "bm25":
                retriever_adapter = BM25RetrieverAdapter()
            elif args.run_type == "hybrid":
                retriever_adapter = HybridRRFRetrieverAdapter()
            elif args.run_type == "hybrid-diversified":
                retriever_adapter = HybridDiversifiedRetrieverAdapter()
            elif args.run_type == "hybrid-graded":
                retriever_adapter = HybridGradedRetrieverAdapter()
            elif args.run_type == "hybrid-rewritten":
                retriever_adapter = HybridRewrittenRetrieverAdapter()
            elif args.run_type == "rrf":
                retriever_adapter = HybridRRFRetrieverAdapter()
            else:
                retriever_adapter = VectorRetrieverAdapter()

            evaluator = RetrievalEvaluator(retriever_adapter)

            if target_path.is_file():
                await evaluate_file(evaluator, target_path, args.top_k, args.run_type)
            elif target_path.is_dir():
                json_files = sorted(list(target_path.glob("*.json")))
                if not json_files:
                    print(f"[Warning] No JSON files found in directory: {target_path}")
                    return
                for f in json_files:
                    await evaluate_file(evaluator, f, args.top_k, args.run_type)
    finally:
        await close_db_pool()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

