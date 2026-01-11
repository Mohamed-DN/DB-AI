# Redis Config

## Scopo del progetto
Define Redis connection settings for the gateway layer.

## Installazione e Setup
Set host, port, and auth in environment or local config. docker-lab uses redis:6379.

## Architettura
The gateway consumes cmd_in and writes result_out.

## Utilizzo
Verify connection with redis-cli ping.
