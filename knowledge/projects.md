# Portfolio Projects

This catalog lists the completed software engineering and DevOps projects developed by Ajay Susanth.

---

## 1. TalentForge

*   **Description**: An AI-powered resume screening, parsing, and candidate ranking system designed to match job descriptions against applicant resumes.
*   **Problem Solved**: Traditional recruiting processes involve manual, slow, and subjective screening of resumes, which scales poorly when handling hundreds of applications.
*   **Major Technologies**:
    *   **Backend**: FastAPI, Celery, Redis, SQLAlchemy (Async), PostgreSQL, pgvector (HNSW Index, cosine similarity)
    *   **Frontend**: React, Tailwind CSS
    *   **AI/ML**: Google Gemini (extracting structured entities), OpenAI embeddings (`text-embedding-3-small` 1536-dimensional vectors), Named Entity Recognition (NER)
*   **Key Engineering Highlights**:
    *   **Asynchronous Ingestion & Processing**: Built a non-blocking parsing engine utilising Celery and Redis with MIME validation, upload limits, and idempotent task orchestration to ensure reliable background processing.
    *   **Multi-Stage Parser**: Integrated document parsing services, Named Entity Recognition (NER) models, and fallback LLMs to generate structured candidate profiles and normalized skills data.
    *   **Hybrid Ranking Engine**: Architected a ranking engine combining semantic vector search (pgvector with HNSW index for cosine similarity) and configurable rule-based scoring.
    *   **Explainability & Inference Caching**: Designed an LLM explainability layer that asynchronously generates candidate match rationales using primary and fallback LLMs, cached in Redis to eliminate redundant inference.

---

## 2. Scalable n8n Architecture on AKS

*   **Description**: A highly available, secure, and autoscaling workflow automation platform deployed on enterprise cloud infrastructure.
*   **Problem Solved**: Standard n8n installations run as single instances, presenting a single point of failure and failing to scale under heavy workflow queues or webhook traffic spikes.
*   **Major Technologies**:
    *   **Orchestration**: Azure Kubernetes Service (AKS), Helm
    *   **Infrastructure**: Microsoft Azure, Terraform (IaC)
    *   **Databases**: PostgreSQL (Flexible Server), Redis (running as a distributed execution queue worker backplane)
    *   **CI/CD & GitOps**: GitHub Actions, ArgoCD, OCI chart packaging
    *   **Observability**: Prometheus, Grafana
    *   **Security**: Calico CNI (Network Policies), OPA Gatekeeper, Secrets Store CSI Driver
*   **Key Engineering Highlights**:
    *   **GitOps & Infrastructure as Code**: Automated provisioning of AKS and supporting cloud resources with modular Terraform scripts. Implemented GitOps-based application deployment using ArgoCD.
    *   **Zero-Trust Networking**: Configured strict Calico Network Policies isolating Postgres, Redis, and internal worker pods, ensuring only the ingress controller has public exposure.
    *   **Dynamic Scaling**: Defined Kubernetes Horizontal Pod Autoscaling (HPA) using KEDA (Kubernetes Event-driven Autoscaling) metrics to scale workers based on Redis queue lengths.

---

## 3. ClassSync

*   **Description**: An automated Google Classroom notification and routing system delivering course updates, announcements, and assignments to students.
*   **Problem Solved**: Students frequently miss time-sensitive academic announcements, assignment deadlines, and grade updates scattered across email notifications and the Google Classroom web portal.
*   **Major Technologies**:
    *   **Languages**: Node.js, JavaScript
    *   **Frameworks**: Express.js
    *   **Workflows**: n8n (visual workflow automation engine)
    *   **Database**: MongoDB
    *   **APIs**: Google Classroom API, Telegram Bot API
*   **Key Engineering Highlights**:
    *   **Webhook & Poll Routing System**: Designed a custom webhook router in n8n to digest and translate incoming Google Classroom feed updates.
    *   **State Tracking**: Implemented automated MongoDB polling states to deduplicate updates and track announcement delivery history, preventing duplicate messages to student channels.
    *   **Telegram Delivery Engine**: Built custom Telegram bot integrations with interactive commands for students to filter announcements by course subject or assignment type.
