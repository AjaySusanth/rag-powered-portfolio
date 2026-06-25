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
from pathlib import Path
from typing import List, Optional

# Add backend directory to sys.path to resolve src imports
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.retrieval.vector_retriever import retrieve as vector_retrieve
from src.models.retrieval_result import RetrievalResult
from src.evaluation.retrieval_evaluator import RetrievalEvaluator, Retriever
from src.models.evaluation_result import EvaluationResult
from src.db.core import close_db_pool


class VectorRetrieverAdapter(Retriever):
    """Adapter to map the vector retrieval retrieve function to the Retriever Protocol."""
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        return await vector_retrieve(query=query, top_k=top_k, project=project)


def save_json_report(result: EvaluationResult, output_path: Path) -> None:
    """Serializes the EvaluationResult dataclass and saves it as a JSON file."""
    data = dataclasses.asdict(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_markdown_report(result: EvaluationResult, output_path: Path) -> None:
    """Generates a human-readable Markdown report summarizing the evaluation."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
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
    print("=" * 40)
    print(f"Project: {result.project}")
    print(f"Questions: {result.total_questions}")
    print("-" * 40)
    print(f"Recall@{result.top_k}: {result.recall * 100:.1f}%")
    print(f"Hit Rate@{result.top_k}: {result.hit_rate * 100:.1f}%")
    print(f"MRR: {result.mrr:.3f}")
    print(f"Average Similarity: {result.average_similarity:.3f}")
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


async def evaluate_file(evaluator: RetrievalEvaluator, file_path: Path, top_k: int) -> None:
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

    # Save reports
    project_slug = result.project
    json_path = ROOT_DIR / "evaluation" / "results" / f"{project_slug}_result.json"
    md_path = ROOT_DIR / "evaluation" / "reports" / f"{project_slug}_report.md"

    save_json_report(result, json_path)
    save_markdown_report(result, md_path)
    print(f"Saved JSON report to: {json_path}")
    print(f"Saved Markdown report to: {md_path}")


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
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"[Error] Target path does not exist: {target_path}")
        sys.exit(1)

    evaluator = RetrievalEvaluator(VectorRetrieverAdapter())

    try:
        if target_path.is_file():
            await evaluate_file(evaluator, target_path, args.top_k)
        elif target_path.is_dir():
            json_files = sorted(list(target_path.glob("*.json")))
            if not json_files:
                print(f"[Warning] No JSON files found in directory: {target_path}")
                return
            for f in json_files:
                await evaluate_file(evaluator, f, args.top_k)
    finally:
        await close_db_pool()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
