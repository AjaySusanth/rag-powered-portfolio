<!-- 
DESIGN DECISION: This file is structured with clear, semantic Markdown headers (H1, H2, H3) and concise bullet points. This layout is designed to support the RAG ingestion pipeline's Layer 1 chunking strategy (256-token chunk size, 32-token overlap). Keeping each section under 200 tokens ensures that the vector and BM25 search queries retrieve coherent, contextually complete blocks of information without bleeding into unrelated topics.
-->

# Ajay's Resume

## Professional Summary
Highly skilled Full-Stack and DevOps Engineer with a strong foundation in building scalable, cloud-native backend systems and automation pipelines. Specialized in FastAPI, React, PostgreSQL, Redis, Docker, and Kubernetes. Passionate about applying AI/ML patterns (such as Retrieval-Augmented Generation) to solve real-world problems and optimizing infrastructure delivery via Infrastructure as Code (IaC) and GitOps.

---

## Technical Skills

### Backend & Databases
- **Languages**: Python (FastAPI, Flask), TypeScript/JavaScript (Node.js, Express)
- **Databases**: PostgreSQL (pgvector, HNSW indexes), Redis (Caching, Session State, Pub/Sub), MongoDB
- **ORM/Query Builders**: Prisma, SQLAlchemy, Alembic

### Frontend
- **Frameworks & Libraries**: React, Next.js, Redux Toolkit, HTML5, CSS3, Tailwind CSS
- **APIs**: REST, Server-Sent Events (SSE), WebSockets, GraphQL

### DevOps & Cloud Infrastructure
- **IaC & Config Management**: Terraform, Ansible
- **Containerization & Orchestration**: Docker, Docker Compose, Kubernetes (AKS), Helm
- **CI/CD & GitOps**: GitHub Actions, ArgoCD
- **Cloud Providers**: Microsoft Azure, AWS
- **Monitoring & Observability**: Prometheus, Grafana, ELK Stack

---

## Professional Experience

### Senior Software Engineer | Cloud Solutions Corp
*June 2024 — Present*
- Architected and built microservices-based backends using **FastAPI** and Node.js, improving system response times by 35%.
- Implemented hybrid caching models using **Redis**, reducing primary database loads by 40% and cutting API latency.
- Migrated legacy database infrastructures to **PostgreSQL**, leveraging optimized indexing strategies and connection pooling.
- Led the containerization transition by writing production-grade multi-stage **Dockerfiles** and managing deployments using **Docker Compose** and **Kubernetes**.

### Software Engineer | InnovateTech
*January 2022 — June 2024*
- Developed responsive, performant user interfaces with **React** and **Tailwind CSS**, increasing user engagement by 20%.
- Integrated robust authentication systems using JSON Web Tokens (JWT) and OAuth2 protocols in backend APIs.
- Built automated CI/CD pipelines via **GitHub Actions** to automate linting, testing, and deployment processes.
- Contributed to database design and migrations using **Prisma ORM**, ensuring schema integrity and performance.

---

## Projects

### RAG-Powered Developer Portfolio ("Ask Ajay")
- Designed and implemented a terminal-style developer portfolio utilizing **FastAPI**, **React**, and **PostgreSQL** with the **pgvector** extension.
- Built a hybrid search engine combining vector search (HNSW index, cosine similarity) and BM25 keyword search, merged via Reciprocal Rank Fusion (RRF) for retrieval precision.
- Engineered a self-healing retrieval pipeline that automatically rewrites low-confidence queries using **Gemini 2.0 Flash**.
- Implemented SSE (Server-Sent Events) streaming for low-latency chat interactions and Redis response caching.

### TalentForge (Full-Stack Platform)
- Built a developer talent platform using **React**, **FastAPI**, and **Prisma ORM** with a PostgreSQL database.
- Implemented complex search and filtering algorithms for matching resumes with job postings.
- Dockerized the frontend and backend microservices to ensure identical dev/prod environments.

### ClassSync (DevOps & Orchestration Project)
- Created a highly available containerized environment utilizing **Kubernetes (AKS)**, **Helm**, and **ArgoCD** for continuous deployment.
- Configured automated infrastructure provisioning via **Terraform** on Azure.
- Structured automated rolling updates and blue-green deployments using GitOps principles.

---

## Education

### Bachelor of Science in Computer Science
*State University | 2018 — 2022*
- Core coursework: Data Structures & Algorithms, Database Management Systems, Software Engineering, Cloud Computing.
