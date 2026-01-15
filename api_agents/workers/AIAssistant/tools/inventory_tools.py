"""
Inventory Search Tools for LangChain Agent
Tools for searching and analyzing the MongoDB inventory
"""
import sys
from pathlib import Path
from langchain_core.tools import tool

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from orchestrator.core.mongo_proxy import MongoProxy

mongo = MongoProxy()


@tool
def search_inventory(search_type: str, value: str) -> str:
    """Search the database inventory by various criteria.
    
    Args:
        search_type: Type of search - 'engine' (ORACLE/POSTGRES), 'environment' (PROD/DEV/STG), 'topology' (PRIMARY/REPLICA/RAC/PDB), 'datacenter'
        value: The value to search for
        
    Returns:
        List of matching databases
    """
    try:
        field_map = {
            'engine': 'identity.engine',
            'environment': 'identity.environment',
            'topology': 'identity.topology',
            'datacenter': 'identity.datacenter',
        }
        
        field = field_map.get(search_type.lower())
        if not field:
            return f"Tipo di ricerca non valido. Usa: engine, environment, topology, datacenter"
        
        value = value.upper()
        results = mongo.execute_eval(f"""
            db.inventory_databases.find({{
                '{field}': {{$regex: '{value}', $options: 'i'}}
            }}, {{
                'identity.db_unique_name': 1,
                'identity.engine': 1,
                'identity.topology': 1,
                'state.status': 1
            }}).toArray()
        """)
        
        if not results:
            return f"Nessun database trovato con {search_type}='{value}'"
        
        output = f"Trovati {len(results)} database con {search_type}='{value}':\n"
        for db in results:
            identity = db.get('identity', {})
            state = db.get('state', {})
            output += f"- {identity.get('db_unique_name')}: {state.get('status')} ({identity.get('engine')} {identity.get('topology')})\n"
        
        return output
    except Exception as e:
        return f"Errore nella ricerca: {str(e)}"


@tool
def get_pdbs_info(cdb_name: str) -> str:
    """Get information about PDBs (Pluggable Databases) for an Oracle CDB.
    
    Args:
        cdb_name: Name of the Container Database (CDB)
        
    Returns:
        List of PDBs with their status
    """
    try:
        results = mongo.execute_eval(f"""
            db.inventory_databases.findOne({{
                'identity.db_unique_name': '{cdb_name}'
            }}, {{
                'pdbs': 1,
                'identity.engine': 1
            }})
        """)
        
        if not results:
            return f"Database '{cdb_name}' non trovato."
        
        if results.get('identity', {}).get('engine') != 'ORACLE':
            return f"'{cdb_name}' non è un database Oracle. I PDB sono disponibili solo per Oracle."
        
        pdbs = results.get('pdbs', [])
        
        if not pdbs:
            return f"Nessun PDB trovato per '{cdb_name}'. Potrebbe essere un database non-CDB o i PDB non sono stati ancora rilevati."
        
        output = f"PDB di {cdb_name} ({len(pdbs)} totali):\n"
        for pdb in pdbs:
            status_icon = "🟢" if pdb.get('status') in ['NORMAL', 'READ WRITE'] else "🟡"
            output += f"  {status_icon} {pdb.get('name')}: {pdb.get('status')}"
            if pdb.get('open_mode'):
                output += f" ({pdb.get('open_mode')})"
            output += "\n"
        
        return output
    except Exception as e:
        return f"Errore: {str(e)}"


@tool
def get_inventory_summary() -> str:
    """Get a summary of the entire database inventory.
    
    Returns:
        Summary statistics of all databases
    """
    try:
        # Get counts by status
        status_counts = mongo.execute_eval("""
            db.inventory_databases.aggregate([
                {$group: {_id: '$state.status', count: {$sum: 1}}}
            ]).toArray()
        """)
        
        # Get counts by engine
        engine_counts = mongo.execute_eval("""
            db.inventory_databases.aggregate([
                {$group: {_id: '$identity.engine', count: {$sum: 1}}}
            ]).toArray()
        """)
        
        # Get counts by environment
        env_counts = mongo.execute_eval("""
            db.inventory_databases.aggregate([
                {$group: {_id: '$identity.environment', count: {$sum: 1}}}
            ]).toArray()
        """)
        
        output = "📊 Riepilogo Inventario Database\n\n"
        
        output += "Per Stato:\n"
        for s in status_counts:
            icon = {"UP": "🟢", "DOWN": "🔴", "WARNING": "🟡"}.get(s['_id'], "⚪")
            output += f"  {icon} {s['_id']}: {s['count']}\n"
        
        output += "\nPer Engine:\n"
        for e in engine_counts:
            icon = "🔶" if e['_id'] == 'ORACLE' else "🐘"
            output += f"  {icon} {e['_id']}: {e['count']}\n"
        
        output += "\nPer Ambiente:\n"
        for env in env_counts:
            output += f"  • {env['_id'] or 'N/A'}: {env['count']}\n"
        
        return output
    except Exception as e:
        return f"Errore nel riepilogo: {str(e)}"
