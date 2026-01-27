"""
Tool Registry Service
Responsible for loading and managing AI tools from MongoDB and local bridging.
"""
import logging
import json
from typing import List, Dict, Any, Callable
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field, create_model

# Import existing tool functions to map them
from api_agents.workers.aiassistant.tools.inventory_tools import search_inventory, get_pdbs_info, get_inventory_summary
from api_agents.workers.aiassistant.tools.action_tools import manage_container, get_container_logs, check_system_health
from api_agents.workers.aiassistant.tools.database_tools import execute_sql_query, explain_query_plan, get_table_schema
from api_agents.workers.aiassistant.tools.orchestration_tools import run_agent, list_agents, manage_gateway

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, mongo_db):
        self.mongo_db = mongo_db
        self.tool_cache: List[Tool] = []
        
        # Map of hardcoded python handlers for "system" tools
        self.system_handlers = {
            "search_inventory": search_inventory,
            "get_pdbs_info": get_pdbs_info,
            "manage_container": manage_container,
            "get_container_logs": get_container_logs,
            "check_system_health": check_system_health,
            "execute_sql_query": execute_sql_query,
            "explain_query_plan": explain_query_plan,
            "get_table_schema": get_table_schema,
            "run_agent": run_agent,
            "list_agents": list_agents
        }

    async def get_tools(self) -> List[Any]:
        """
        Fetch all available tools (System + Dynamic from MongoDB).
        Returns a list of LangChain-compatible tools.
        """
        tools = []
        
        # 1. Load System Tools
        # Check if we have configuration in Mongo, otherwise load all defaults
        try:
            enabled_system_tools = set()
            config_cursor = self.mongo_db['ai_system_tools'].find({"enabled": True})
            found_configs = False
            async for doc in config_cursor:
                found_configs = True
                enabled_system_tools.add(doc['name'])
            
            for name, func in self.system_handlers.items():
                # If no config exists, load everything (backward compatibility). 
                # If config exists, only load what's enabled.
                if not found_configs or name in enabled_system_tools:
                    tools.append(func)
        except Exception as e:
            logger.warning(f"Failed to load system tool config, loading all defaults: {e}")
            for func in self.system_handlers.values():
                tools.append(func)
            
        # 2. Load Dynamic Tools from MongoDB (e.g., SQL Templates)
        try:
            # Assume collection 'ai_tools' exists
            # Doc schema: { "name": str, "description": str, "type": "sql_template", "sql": str, "params": dict }
            cursor = self.mongo_db['ai_tools'].find({"enabled": True})
            async for tool_doc in cursor:
                if tool_doc.get('type') == 'sql_template':
                    dynamic_tool = self._create_sql_tool(tool_doc)
                    if dynamic_tool:
                        tools.append(dynamic_tool)
        except Exception as e:
            logger.error(f"Failed to load dynamic tools from MongoDB: {e}")
            
        self.tool_cache = tools
        return tools

    def _create_sql_tool(self, doc: Dict) -> StructuredTool:
        """Creates a LangChain tool from a MongoDB SQL template document"""
        name = doc.get('name')
        description = doc.get('description')
        sql_template = doc.get('sql')
        params_schema = doc.get('params', {}) # Dict of param_name -> type
        
        # Create Pydantic model dynamically for arguments
        fields = {k: (str, Field(description=f"Parameter {k}")) for k in params_schema.keys()}
        # Note: simplistic type handling, assuming strings for now. comprehensive mapping needed for int/bool.
        ArgsModel = create_model(f"{name}Args", **fields)

        def execution_wrapper(**kwargs):
            # 1. Format SQL
            try:
                final_sql = sql_template.format(**kwargs)
            except KeyError as e:
                return f"Error building query: Missing parameter {e}"
            
            # 2. Execute via existing SQL handler (assumed allowed)
            # We assume the AI passes a target_db/container kwarg or we default to something
            # For this simple implementation, we might need to inject the target DB context.
            # Use 'execute_sql_query' logic directly or reuse it.
            # LIMITATION: Dynamic SQL tools need a target database context.
            # We'll mandate 'target_db' as a required parameter if not present in template.
            
            target_db = kwargs.get('target_db') or kwargs.get('db_name')
            if not target_db:
                return "Error: Dynamic SQL tool execution requires 'target_db' or 'db_name' parameter."
                
            return execute_sql_query(query=final_sql, db_name=target_db)

        return StructuredTool.from_function(
            func=execution_wrapper,
            name=name,
            description=description,
            args_schema=ArgsModel
        )
