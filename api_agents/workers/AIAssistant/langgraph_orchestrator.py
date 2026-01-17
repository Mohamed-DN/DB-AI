"""
LangGraph Orchestrator - Multi-Agent AI DBA Workflow
Orchestrates Diagnostic, Remediation, and Execution agents for database alerts.
"""
import json
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LangGraphDBA")

# =============================================================================
# State Definition
# =============================================================================

class DBAState(TypedDict):
    """Accurate state of the DBA workflow"""
    # Inputs
    db_name: str
    alert_info: Dict[str, Any]
    
    # Process State
    diagnosis: Optional[Dict[str, Any]]
    remediation_plan: Optional[Dict[str, Any]]
    
    # Flags
    is_false_positive: bool
    requires_human_approval: bool
    approved: bool
    execution_result: Optional[str]
    
    # Conversation history
    messages: List[Any]

# =============================================================================
# Agent Nodes
# =============================================================================

def diagnostic_agent_node(state: DBAState):
    """
    Step 1: Diagnostic Agent
    Analyzes the alert and database context to determine root cause and validity.
    """
    logger.info(f"🔍 Diagnosing alert for {state['db_name']}...")
    
    # Initialize LLM (DeepSeek R1 for reasoning or generic model)
    # Using a generic name first, can be configured
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0.2)
    
    alert_str = json.dumps(state['alert_info'], indent=2)
    
    prompt = f"""
    You are an Expert DBA Diagnostician. Analyze this database alert.
    
    DATABASE: {state['db_name']}
    ALERT: {alert_str}
    
    Perform a root cause analysis. Determine if this is a false positive.
    
    Respond STRICTLY in JSON format:
    {{
      "root_cause": "Detailed explanation of the issue",
      "severity": "CRITICAL|WARNING|INFO",
      "is_false_positive": boolean,
      "confidence_score": 0.0-1.0,
      "recommended_action_type": "SQL|RESTART|SCALE|IGNORE"
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        # Strip thinking tokens if present (DeepSeek specific)
        if "</think>" in content:
            content = content.split("</think>")[-1]
            
        diagnosis = json.loads(content.strip().strip('`').replace('json', ''))
        
        logger.info(f"✅ Diagnosis complete: {diagnosis.get('root_cause')}")
        
        return {
            "diagnosis": diagnosis,
            "is_false_positive": diagnosis.get("is_false_positive", False)
        }
    except Exception as e:
        logger.error(f"❌ Diagnostic failed: {e}")
        return {
            "diagnosis": {"root_cause": f"Analysis failed: {str(e)}", "severity": "UNKNOWN"},
            "is_false_positive": False # Assume true alert on error
        }

def remediation_agent_node(state: DBAState):
    """
    Step 2: Remediation Agent
    Proposes a step-by-step plan to fix the diagnosed issue.
    """
    if state.get("is_false_positive"):
        logger.info("⏩ Skipping remediation (False Positive)")
        return {"remediation_plan": {"steps": ["Mark as False Positive"], "commands": []}}
        
    logger.info(f"🛠️ Planning remediation for {state['db_name']}...")
    
    llm = ChatOllama(model="qwen2.5-coder:14b", temperature=0.1)
    
    diag_str = json.dumps(state['diagnosis'], indent=2)
    
    prompt = f"""
    You are a Senior DBA. Create a remediation plan for this issue.
    
    DATABASE: {state['db_name']}
    DIAGNOSIS: {diag_str}
    
    Provide a safe, step-by-step plan.
    
    Respond STRICTLY in JSON format:
    {{
      "title": "Short title of fix",
      "steps": ["step 1", "step 2"],
      "commands": ["SQL or Bash commands to execute"],
      "risk_level": "HIGH|MEDIUM|LOW",
      "requires_human_approval": boolean
    }}
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if "</think>" in content:
            content = content.split("</think>")[-1]

        plan = json.loads(content.strip().strip('`').replace('json', ''))
        
        logger.info(f"✅ Plan created: {plan.get('title')}")
        
        return {
            "remediation_plan": plan,
            "requires_human_approval": plan.get("requires_human_approval", True)
        }
    except Exception as e:
        logger.error(f"❌ Remediation planning failed: {e}")
        return {
            "remediation_plan": {"title": "Manual Intervention Required", "commands": []},
            "requires_human_approval": True
        }

def execution_agent_node(state: DBAState):
    """
    Step 3: Execution Agent (Placeholder for now)
    Executes the approved remediation plan.
    """
    logger.info(f"⚡ Executing fix for {state['db_name']}...")
    
    # integration with connection router would happen here
    # For phase 4 MVP, we simulate execution
    
    return {
        "execution_result": "Simulated Success: Commands executed via Agent API."
    }

def human_approval_node(state: DBAState):
    """
    Step: Human Approval (Wait State)
    In a real system, this would persist state and wait.
    For this demo flow, we route here and stop.
    """
    logger.info("🛑 Waiting for Human Approval...")
    return {} # State doesn't change, just a checkpoint

# =============================================================================
# Conditional Logic
# =============================================================================

def route_after_diagnosis(state: DBAState):
    if state.get("is_false_positive"):
        return "auto_resolve"
    return "remediate"

def route_after_remediation(state: DBAState):
    if state.get("requires_human_approval"):
        return "human_approval"
    return "execute"

# =============================================================================
# Graph Construction
# =============================================================================

def build_dba_graph():
    workflow = StateGraph(DBAState)
    
    # Add Nodes
    workflow.add_node("diagnose", diagnostic_agent_node)
    workflow.add_node("remediate", remediation_agent_node)
    workflow.add_node("execute", execution_agent_node)
    workflow.add_node("auto_resolve", lambda x: {"execution_result": "Marked as FP"}) # Simple node
    workflow.add_node("human_approval", human_approval_node)
    
    # Set Entry
    workflow.set_entry_point("diagnose")
    
    # Add Edges
    workflow.add_conditional_edges(
        "diagnose",
        route_after_diagnosis,
        {
            "auto_resolve": "auto_resolve",
            "remediate": "remediate"
        }
    )
    
    workflow.add_conditional_edges(
        "remediate",
        route_after_remediation,
        {
            "human_approval": "human_approval",
            "execute": "execute"
        }
    )
    
    workflow.add_edge("execute", END)
    workflow.add_edge("auto_resolve", END)
    workflow.add_edge("human_approval", END) # In real app, this would be a breakpoint
    
    return workflow.compile()

# Global Compiled Instance
dba_workflow = build_dba_graph()
