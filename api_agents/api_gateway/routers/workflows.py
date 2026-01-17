"""
Workflows Router - Multi-Agent AI Workflow Endpoints (LangGraph)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api_agents.workers.AIAssistant.langgraph_orchestrator import dba_workflow, DBAState
from ..services.mongo_service import get_mongo_service
import uuid

router = APIRouter()

# In-memory storage for workflow results (in production use Redis/Mongo)
# Key: execution_id -> State
WORKFLOW_RESULTS = {}

@router.post("/workflows/analyze_alert/{alert_id}")
async def analyze_alert_workflow(alert_id: str, background_tasks: BackgroundTasks):
    """
    Trigger the Multi-Agent DBA Workflow for a specific alert.
    Steps: Diagnose -> Remediation Plan -> (Approval) -> Execute
    """
    try:
        mongo = get_mongo_service()
        # Fetch alert to verify existence (and get details if not passed)
        # For now, we simulate alert info if not fetching from DB directly or use dummy
        # In real app: alert = await mongo.get_alert(alert_id)
        
        # Simulating alert retrieval for the workflow input
        alert_info = {
            "id": alert_id,
            "message": "High CPU usage on Oracle DB",
            "host": "nexi-oracle-cairo-primary",
            "state": "CRITICAL"
        }
        
        execution_id = str(uuid.uuid4())
        
        initial_state: DBAState = {
            "db_name": alert_info["host"],
            "alert_info": alert_info,
            "diagnosis": None,
            "remediation_plan": None,
            "is_false_positive": False,
            "requires_human_approval": False,
            "approved": False,
            "execution_result": None,
            "messages": []
        }
        
        WORKFLOW_RESULTS[execution_id] = {"status": "running", "state": initial_state}
        
        background_tasks.add_task(run_workflow_async, execution_id, initial_state)
        
        return {
            "execution_id": execution_id,
            "status": "submitted",
            "workflow": "DBA_Multi_Agent_Analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_workflow_async(execution_id: str, initial_state: DBAState):
    """Helper to run synchronous LangGraph in background"""
    try:
        # LangGraph invoke is synchronous currently/mostly
        # If async support is experimental, we wrap or use invoke
        result_state = dba_workflow.invoke(initial_state)
        WORKFLOW_RESULTS[execution_id] = {"status": "completed", "state": result_state}
    except Exception as e:
        WORKFLOW_RESULTS[execution_id] = {"status": "failed", "error": str(e)}

@router.get("/workflows/{execution_id}")
async def get_workflow_status(execution_id: str):
    """Get the status and result of a workflow execution"""
    if execution_id not in WORKFLOW_RESULTS:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return WORKFLOW_RESULTS[execution_id]
