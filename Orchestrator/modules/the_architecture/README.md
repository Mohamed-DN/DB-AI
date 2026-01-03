# THE ARCHITECTURE Module

AI module responsible for understanding system topology and relationships.

## Capabilities

- Understands RAC, Data Guard, GoldenGate topologies
- Maps dependencies between databases
- Knows which DBs serve which business services
- Provides architectural context for troubleshooting

## Queries It Can Answer

- "What databases are part of the NZSEP cluster?"
- "Show me the Data Guard topology for PROD databases"
- "Which services depend on this database?"
