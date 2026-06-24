## Professional Summary
Ajay Susanth is a Software Engineer and final-year B.Tech student with hands-on experience building and operating production-style systems end to end—from cloud infrastructure to running services. Ajay Susanth has experience designing and provisioning Azure infrastructure with Terraform, building distributed backend systems with FastAPI and Express.js, and re-architecting monolithic deployments into scalable, observable Kubernetes platforms with CI/CD and GitOps. Ajay Susanth specializes in owning projects from infrastructure to production, including application development, containerization, orchestration, and continuous integration and deployment.

## Technical Skills
The technical skills of Ajay Susanth include:
- Programming Languages: Python, JavaScript, TypeScript
- Backend Frameworks: FastAPI, Express.js (Node.js)
- Frontend Frameworks: React, HTML5, CSS3, Tailwind CSS
- Databases & Vector Stores: PostgreSQL, pgvector (HNSW index, cosine similarity), Redis (caching, queueing), MongoDB
- Database Abstractions & ORMs: Prisma ORM, Sequelize
- Containerization & Orchestration: Docker, Kubernetes, Azure Kubernetes Service (AKS), Helm
- Continuous Integration & Deployment (CI/CD) and GitOps: GitHub Actions, ArgoCD, OCI packaging
- Cloud & Infrastructure as Code (IaC): Microsoft Azure, Terraform, Azure Container Apps, Azure Container Registry, Azure Key Vault, Azure Blob Storage
- Automation Tools: n8n automation, Telegram Bot API
- Monitoring & Observability: Prometheus, Grafana, Calico Network Policies, OPA Gatekeeper, Secrets Store CSI Driver

## Backend Engineering Experience
Ajay Susanth has backend engineering experience focused on developing distributed APIs, background task workers, and database architectures. In his projects, Ajay Susanth built a multi-tenant REST API using Express.js with classroom-scoped authorization for educational workflows, and implemented an asynchronous candidate resume ingestion pipeline using FastAPI, Celery, and Redis. His backend engineering work includes implementing MIME type validation, file upload limits (10 MB), and idempotent task orchestration to ensure reliable background processing. Ajay Susanth has designed database layers using PostgreSQL and MongoDB, utilizing Prisma ORM to manage migrations, schema integrity, and type-safe transactions. He has also built API security middlewares, service-to-service authentication using static keys, and JSON Web Token (JWT) authorization guards.

## Cloud and DevOps Experience
Ajay Susanth has cloud infrastructure and DevOps experience specializing in Microsoft Azure, Kubernetes, and automated deployment pipelines. He has experience provisioning cloud environments using Terraform Infrastructure as Code (IaC), including resource setups for Azure Container Apps, Azure Container Registry (ACR), Azure Key Vault, and PostgreSQL Flexible Server. In Kubernetes, Ajay Susanth has deployed workloads to Azure Kubernetes Service (AKS), authoring custom Helm charts to split n8n monolithic deployments into distributed UI, webhook, and worker containers. He has built automated GitOps continuous deployment pipelines using GitHub Actions, Helm, and ArgoCD with immutable OCI versioning (`1.0.0-<SHA>`). His cluster security and hardening work includes writing Calico network policies to enforce default-deny controls, using the Secrets Store CSI driver to mount Azure Key Vault secrets, and defining Open Policy Agent (OPA) Gatekeeper validating admission webhooks. Ajay Susanth also configures Horizontal Pod Autoscaling based on queue depth using KEDA, and monitors systems using Prometheus alerting rules and Grafana dashboards.

## AI and Machine Learning Experience
Ajay Susanth has AI and Machine Learning experience through his formal education (B.Tech in Artificial Intelligence and Machine Learning) and project implementations. He has built intelligent text processing pipelines, integrating Azure Document Intelligence, HuggingFace Named Entity Recognition (NER) models, and LLM providers like Gemini and Groq (using llama-3.1-70b as a fallback). In the domain of information retrieval and vector search, Ajay Susanth has architected hybrid search engines combining 1536-dimensional OpenAI embeddings (`text-embedding-3-small`) with rule-based scoring (40% semantic and 60% rule-based weights). He has implemented similarity searches using pgvector and HNSW index indexing for cosine similarity calculations. Additionally, Ajay Susanth has designed LLM explainability layers to asynchronously generate ranked-candidate selection rationales, caching the inference results in Redis with a 7-day TTL to eliminate redundant LLM API calls.

## Automation and Workflow Engineering Experience
Ajay Susanth has automation and workflow engineering experience centered around n8n automation and third-party API integrations. He has experience designing complex n8n workflows that process events out-of-band, including webhook-triggered notification pipelines and scheduled cron reminder systems. In his projects, Ajay Susanth integrated n8n with an Express.js backend using service-to-service authentication keys to orchestrate automated Telegram notifications to students and poll for upcoming deadlines. He has experience designing Telegram command routers within n8n workflows to handle user interactions (such as chat-ID binding and task queries) while circumventing Telegram's single-webhook restriction. Furthermore, Ajay Susanth has experience operating and scaling n8n itself, having re-engineered monolithic n8n setups into split UI, webhook, and worker container structures running on Kubernetes.

## Project: TalentForge
TalentForge is an AI-powered smart talent selection and resume parsing platform built by Ajay Susanth. The project is implemented using a FastAPI backend, a React frontend, PostgreSQL with pgvector, Gemini and Groq LLMs, and Redis for caching.
Key technical features built by Ajay Susanth in TalentForge include:
- An asynchronous resume ingestion pipeline using FastAPI, Celery, and Redis with MIME validation, 10 MB file size limits, and idempotent task orchestration.
- A multi-stage LLM parsing pipeline integrating Azure Document Intelligence, HuggingFace Named Entity Recognition (NER), and Gemini/Groq fallback models to parse unstructured resumes into normalized candidate profiles.
- A hybrid ranking engine using 1536-dimensional OpenAI embeddings and a custom scoring algorithm (40% semantic similarity / 60% rule-based metrics), backed by PostgreSQL and pgvector with an HNSW index for cosine similarity search.
- An LLM explainability layer that asynchronously generates natural language rationales for ranked candidates (using Gemini as primary and Groq as fallback), cached in Redis with a 7-day TTL to optimize API costs.

## Project: Automated Classwork
Automated Classwork (also referred to as ClassSync) is a multi-tenant educational automation platform built by Ajay Susanth. The project is implemented using Express.js, n8n workflows, Terraform, Microsoft Azure, and PostgreSQL.
Key technical features built by Ajay Susanth in Automated Classwork include:
- A multi-tenant REST API built on Express.js featuring classroom-scoped authorization policies for classroom assignment creation and student grading workflows.
- Workflow automation using n8n for webhook-driven notification dispatching and scheduled email/Telegram reminders, communicating securely with the backend via internal API keys.
- Infrastructure as Code provisioning using Terraform to deploy Azure Container Apps, Azure Container Registry, PostgreSQL Flexible Server, Log Analytics, and Azure Key Vault.
- Containerized deployments using multi-stage Docker builds behind an Nginx reverse proxy, and a Telegram-first account-linking flow using short-lived JWT tokens for secure chat-ID binding.

## Project: Scalable n8n Architecture on AKS
Scalable n8n Architecture on AKS is a DevOps and container orchestration project built by Ajay Susanth. The project is implemented using Azure Kubernetes Service (AKS), Kubernetes, Terraform, ArgoCD, and Prometheus.
Key technical features built by Ajay Susanth in Scalable n8n Architecture on AKS include:
- Re-architecting a monolithic n8n deployment into independently scalable UI (`n8n-main`), webhook (`n8n-webhook`), and worker (`n8n-worker`) workloads running on AKS, provisioned via modular Terraform configurations.
- Authoring a custom Helm chart and establishing a GitOps continuous deployment pipeline using GitHub Actions, Helm, and ArgoCD with immutable version tags (`1.0.0-<SHA>`).
- Implementing KEDA (Kubernetes Event-driven Autoscaling) to scale worker pods dynamically from 1 to 10 replicas based on Redis queue depth, coupled with Prometheus alerts and Grafana dashboards for cluster visibility.
- Hardening cluster security through Calico Network Policies enforcing default-deny traffic controls, Azure Key Vault Secrets Store CSI driver integration to mount secrets, and 3 OPA Gatekeeper validating admission policies.

## Education
The educational background of Ajay Susanth consists of:
- Degree: Bachelor of Technology (B.Tech) in Artificial Intelligence and Machine Learning
- University: APJ Abdul Kalam Technological University
- College: Mar Athanasius College of Engineering, Kothamangalam, Kerala, India
- Timeline: 2023 — 2027
- Academic Performance: 8.78 CGPA

## Certifications
Ajay Susanth holds the following professional certifications:
- Oracle Cloud Infrastructure Certified Foundations Associate, obtained in 2025
- Deploy Kubernetes Applications on Google Cloud (Google Cloud Skill Badge), obtained in 2025

## Project-to-Skill Mapping
The following lists map the projects completed by Ajay Susanth to the specific technologies and engineering skills demonstrated:
- Kubernetes & Container Orchestration: Demonstrated in Scalable n8n Architecture on AKS (AKS, Helm, ArgoCD, KEDA) and TalentForge/Automated Classwork (Docker containerization).
- Terraform & Infrastructure as Code: Demonstrated in Scalable n8n Architecture on AKS (AKS infrastructure) and Automated Classwork (Azure Container Apps and databases).
- AI & Machine Learning Integration: Demonstrated in TalentForge (OpenAI Embeddings, pgvector, Gemini, Groq, HuggingFace NER, Azure Document Intelligence).
- Backend Engineering & Databases: Demonstrated in TalentForge (FastAPI, Celery, Redis, pgvector) and Automated Classwork (Express.js, Prisma ORM, PostgreSQL).
- Workflow & Automation Orchestration: Demonstrated in Scalable n8n Architecture on AKS (decoupling and running n8n at scale) and Automated Classwork (integrating n8n triggers and webhooks).
