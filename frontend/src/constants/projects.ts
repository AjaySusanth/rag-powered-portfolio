export interface Project {
  name: string;
  shortDescription: string;
  problemSolved: string;
  technologies: string[];
  highlights: string[];
  githubUrl: string;
  liveUrl?: string;
  aiPrompt: string;
}

export const PROJECTS: Project[] = [
  {
    name: "TalentForge",
    shortDescription: "An AI-powered resume screening, parsing, and candidate ranking system.",
    problemSolved: "Replaces manual, subjective resume screening workflows by extracting high-fidelity structured profiles and performing semantic rank-ordering.",
    technologies: ["FastAPI", "Celery", "Redis", "PostgreSQL", "pgvector", "React", "Google Gemini", "OpenAI Embeddings"],
    highlights: [
      "Twelve-step stateful parsing pipeline utilizing layout-aware OCR (Azure Document Intelligence) and multi-model LLM orchestration.",
      "Deterministic data canonicalization for experience indices and date calculations combined with semantic vector search.",
      "CELERY background task workers running with custom fault tolerance and graceful degradations."
    ],
    githubUrl: "https://github.com/AjaySusanth/talentforge",
    aiPrompt: "Explain the resume parsing pipeline in TalentForge."
  },
  {
    name: "ClassSync",
    shortDescription: "An automated notification and routing system for Google Classroom updates.",
    problemSolved: "Consolidates academic updates, deadlines, and announcement streams which are otherwise scattered across Classroom portals.",
    technologies: ["Node.js", "Express.js", "n8n", "MongoDB", "Telegram Bot API", "Azure Container Apps (ACA)"],
    highlights: [
      "Dynamic webhook and poll routing engine capturing classroom events in real-time.",
      "Idempotency state machine in MongoDB ensuring that notifications are processed and sent exactly once.",
      "Integrated Telegram Bot delivery system with localized subscriber groupings and filters."
    ],
    githubUrl: "https://github.com/AjaySusanth/classsync",
    aiPrompt: "What deployment strategy is used in ClassSync?"
  },
  {
    name: "Scalable n8n Architecture on AKS",
    shortDescription: "A production-grade, self-hosted DevOps and GitOps infrastructure project.",
    problemSolved: "Transforms n8n's monolithic deployment into highly available, independently autoscaled microservices on Kubernetes.",
    technologies: ["Azure Kubernetes Service (AKS)", "Terraform", "Helm", "ArgoCD", "KEDA", "Prometheus", "Grafana", "Azure Key Vault"],
    highlights: [
      "Decoupled n8n execution into active UI, webhook receiver, and async workers running behind zero-trust NetworkPolicies.",
      "GitOps delivery using ArgoCD for automated sync and self-healing cluster states.",
      "Queue-depth autoscaling with KEDA monitoring Redis and scaling workers from 1 to 10 replicas."
    ],
    githubUrl: "https://github.com/AjaySusanth/n8n-production-platform",
    aiPrompt: "Which projects did Ajay deploy and where?"
  }
];
