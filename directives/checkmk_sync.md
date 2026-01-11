# Directive: checkmk_sync

## Scopo del progetto
Import metrics and alerts from CheckMK.

## Installazione e Setup
Configure CheckMK endpoint and credentials in env or config files.

## Architettura
CheckMK Bridge fetches metrics and writes to monitoring_alerts and inventory_databases.

## Utilizzo
Start checkmk_bridge via Agents panel or POST /api/agents/start/checkmk_bridge
