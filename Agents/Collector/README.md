# SADA-COLLECTOR Agent

The **Collector** agent performs deep inspection of identified services.

## Functions

1. **Task Execution**: Reads targets from `Discovery_Queue`.
2. **Deep Inspection**: Connects to databases (Oracle, Postgres) to retrieve detailed configuration.
3. **Normalization**: Uses AI to structure data into the standard CMDB JSON format.
4. **Storage**: Saves the final inventory to `CMDB_Inventory`.

## Resources

- **resources/oracle_scripts/**: SQL scripts for Oracle metadata extraction (AWR, Metrics, Locks, etc.).
- **steps.md**: Implementation steps/notes.
