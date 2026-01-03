#!/bin/bash
# Simula output di comando Oracle per test
# Questo script viene chiamato dal Collector per testare l'estrazione dati

echo "DB_NAME         DB_UNIQUE_NAME  DATABASE_ROLE    OPEN_MODE        VERSION     INSTANCE_NAME   HOST_NAME"
echo "--------------- --------------- ---------------- ---------------- ----------- --------------- ---------------"
echo "TESTDB          TESTDB_PROD     PRIMARY          READ WRITE       19.16.0.0   TESTDB1         $(hostname)"
