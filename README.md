# RAG-Powered Developer Portfolio

An AI-powered developer portfolio built to showcase projects, technical decisions, and engineering experience through interactive conversations.

This project is being developed as a learning-focused exploration of:

* Retrieval-Augmented Generation (RAG)
* Search Systems
* Backend Engineering
* DevOps & Cloud Infrastructure
* AI Application Development

The goal is to create a portfolio that goes beyond a traditional resume by allowing visitors to explore projects, architecture decisions, and implementation details through natural language.

## Status

🚧 Work in Progress

Currently in the planning and architecture phase.

## Tech Stack

* FastAPI
* React
* PostgreSQL
* Redis
* Docker

Additional technologies may be introduced as the project evolves.

## Knowledge Ingestion

The portfolio uses an offline indexing script to ingest projects and identity files into the `pgvector` store. To run ingestion, set your `PYTHONPATH` and use the local virtual environment:

```bash
# Ingest root global identity files (resume.md, about-me.md, faq.md, projects.md, stack.md, hire.md)
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py __global__

# Ingest a specific project (e.g., talentforge)
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py talentforge
```

## Development Philosophy

This project is being built with a strong emphasis on:

* Understanding over code generation
* Documentation-first development
* Production-grade engineering practices
* System design and architectural thinking

## Roadmap

* [ ] Define architecture and knowledge base structure
* [ ] Build ingestion pipeline
* [ ] Implement retrieval system
* [ ] Develop conversational interface
* [ ] Add observability and deployment workflows
* [ ] Deploy publicly

---

Building in public and learning along the way.
