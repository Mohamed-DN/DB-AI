# Repository Manifest

## Scopo del progetto
This document maps the repository structure for the v3 branch.

## Installazione e Setup
No setup required for this document. See README.md for environment setup.

## Architettura
- Agents/: monitoring and discovery agents
- WebInterface/: FastAPI backend and React frontend
- Orchestrator/: LLM and RAG services
- MongoDB/: CMDB schemas and collection docs
- docker-lab/: local infra via docker-compose
- Gateway/: Redis based gateway layer
- scripts/: automation helpers
- Tests/: integration scenarios
- directives/: operational directives used by the AI layer

## Utilizzo
Use this file as an index when onboarding or locating components.
