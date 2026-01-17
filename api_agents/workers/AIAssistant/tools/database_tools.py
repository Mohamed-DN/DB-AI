"""
Database Query Tools for LangChain Agent
Tools for interacting with database inventory in MongoDB
"""
import os
import sys
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from orchestrator.core.mongo_proxy import MongoProxy

mongo = MongoProxy()


@tool
def search_databases(query: str) -> str:
    """Search databases by name pattern.
    
    Args:
        query: Part of the database name to search for (case-insensitive)
        
    Returns:
        List of matching databases with their status
    """
    try:
        # Use regex search in MongoDB
        results = mongo.execute_eval(f"""
            db.inventory_databases.find({{
                'identity.db_unique_name': {{$regex: '{query}', $options: 'i'}}
            }}, {{
                'identity.db_unique_name': 1,
                'identity.engine': 1,
                'state.status': 1,
                'identity.environment': 1
            }}).toArray()
        """)
        
        if not results:
            return f"Nessun database trovato con '{query}' nel nome."
        
        output = f"Trovati {len(results)} database:\n"
        for db in results:
            identity = db.get('identity', {})
            state = db.get('state', {})
            output += f"- {identity.get('db_unique_name')}: {state.get('status', 'UNKNOWN')} ({identity.get('engine', 'N/A')}, {identity.get('environment', 'N/A')})\n"
        
        return output
    except Exception as e:
        return f"Errore nella ricerca: {str(e)}"


@tool
def get_database_status(db_name: str) -> str:
    """Get detailed status information for a specific database.
    
    Args:
        db_name: The exact name of the database
        
    Returns:
        Detailed status information including metrics
    """
    try:
        results = mongo.execute_eval(f"""
            db.inventory_databases.findOne({{
                'identity.db_unique_name': '{db_name}'
            }})
        """)
        
        if not results:
            return f"Database '{db_name}' non trovato nell'inventario."
        
        identity = results.get('identity', {})
        state = results.get('state', {})
        config = results.get('configuration', {})
        metrics = state.get('metrics', {})
        
        output = f"""Database: {identity.get('db_unique_name')}
Engine: {identity.get('engine')}
Topology: {identity.get('topology')}
Status: {state.get('status')}
Environment: {identity.get('environment', 'N/A')}
Last Seen: {state.get('last_seen', 'N/A')}

Configuration:
- Version: {config.get('version', 'N/A')}
- Open Mode: {config.get('open_mode', 'N/A')}
- Log Mode: {config.get('log_mode', 'N/A')}

Host Metrics:
- Hostname: {metrics.get('hostname', 'N/A')}
- OS: {metrics.get('os_type', 'N/A')}
- CPU: {metrics.get('cpu_count', 'N/A')} cores
- Memory: {metrics.get('memory_gb', 'N/A')} GB
"""
        
        # Add PDB info for Oracle
        pdbs = results.get('pdbs', [])
        if pdbs:
            output += f"\nPDBs ({len(pdbs)}):\n"
            for pdb in pdbs:
                output += f"- {pdb.get('name')}: {pdb.get('status')}\n"
        
        return output
    except Exception as e:
        return f"Errore nel recupero stato: {str(e)}"


@tool
def list_databases_by_status(status: str) -> str:
    """List all databases with a specific status.
    
    Args:
        status: The status to filter by (UP, DOWN, WARNING, UNKNOWN, MISSING)
        
    Returns:
        List of databases with that status
    """
    try:
        status = status.upper()
        results = mongo.execute_eval(f"""
            db.inventory_databases.find({{
                'state.status': '{status}'
            }}, {{
                'identity.db_unique_name': 1,
                'identity.engine': 1,
                'identity.environment': 1,
                'state.last_seen': 1
            }}).toArray()
        """)
        
        if not results:
            return f"Nessun database con stato '{status}'."
        
        output = f"Database con stato {status} ({len(results)} totali):\n"
        for db in results:
            identity = db.get('identity', {})
            state = db.get('state', {})
            output += f"- {identity.get('db_unique_name')} ({identity.get('engine')}) - Last seen: {state.get('last_seen', 'N/A')}\n"
        
        return output
    except Exception as e:
        return f"Errore: {str(e)}"


@tool
def get_database_metrics(db_name: str) -> str:
    """Get performance metrics for a database.
    
    Args:
        db_name: Name of the database
        
    Returns:
        Performance metrics if available
    """
    try:
        results = mongo.execute_eval(f"""
            db.inventory_databases.findOne({{
                'identity.db_unique_name': '{db_name}'
            }}, {{
                'metrics': 1,
                'state.metrics': 1,
                'tablespaces': 1
            }})
        """)
        
        if not results:
            return f"Database '{db_name}' non trovato."
        
        metrics = results.get('metrics', results.get('state', {}).get('metrics', {}))
        tablespaces = results.get('tablespaces', [])
        
        output = f"Metriche per {db_name}:\n"
        
        if metrics:
            output += f"""
Host: {metrics.get('hostname', 'N/A')}
OS: {metrics.get('os_type', 'N/A')}
CPU Cores: {metrics.get('cpu_count', 'N/A')}
Memory: {metrics.get('memory_gb', 'N/A')} GB
"""
        
        if tablespaces:
            output += f"\nTablespaces ({len(tablespaces)}):\n"
            for ts in tablespaces[:5]:  # Limit to first 5
                used = float(ts.get('used_percent', 0))
                status = "⚠️" if used > 80 else "✅"
                output += f"- {ts.get('tablespace_name')}: {used:.1f}% utilizzato {status}\n"
            if len(tablespaces) > 5:
                output += f"... e altri {len(tablespaces) - 5} tablespaces\n"
        
        return output if len(output) > 50 else f"Nessuna metrica disponibile per {db_name}"
    except Exception as e:
        return f"Errore: {str(e)}"


@tool
def execute_sql_query(query: str, db_name: str) -> str:
    """Execute a raw SQL query against a specific database.
    WARNING: Use only for read-only queries (SELECT).
    """
    return f"Simulated Result: [1] Row(status='active', db='{db_name}')"

@tool
def explain_query_plan(query: str, db_name: str) -> str:
    """Get the execution plan for a query."""
    return f"Simulated Plan for {db_name}: TABLE ACCESS FULL"

@tool
def get_table_schema(table_name: str, db_name: str) -> str:
    """Get the schema definition of a table."""
    return f"Schema for {table_name}: id INT, name VARCHAR(50)"
