# Docker Lab Environment

## Scopo del progetto
Local infrastructure for Nexi DBA AI development and tests.

## Installazione e Setup
cd docker-lab
docker-compose up -d

## Architettura
Services: MongoDB, Mongo Express, Redis, Ollama, Open WebUI, Qdrant,
gateway containers, Postgres clusters (Milano and Bratislava), Oracle (Cairo).

## Utilizzo
- docker-compose ps
- docker-compose down
- Default ports: 27017 (MongoDB), 8081 (Mongo Express), 6379 (Redis),
  6333 (Qdrant), 11434 (Ollama)
