"""
RAG Pipeline - Retrieval Augmented Generation for Database Diagnostics
Combines Qdrant (knowledge retrieval) + Ollama (generation) for intelligent analysis.
"""

import sys
import os

# Add path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from typing import List, Dict, Any, Optional
from llm.client.ollama_client import OllamaClient
from Orchestrator.vector_db.qdrant_client import QdrantClient, generate_simple_embedding


class RAGPipeline:
    """
    Retrieval Augmented Generation Pipeline.
    
    Flow:
    1. User Query / Alert Context
    2. Embed query and search Qdrant for relevant docs
    3. Combine retrieved context with original query
    4. Send augmented prompt to Ollama
    5. Return AI-generated response
    """
    
    def __init__(self):
        self.llm = OllamaClient()
        self.vector_db = QdrantClient()
        
        # System prompts for different use cases
        self.system_prompts = {
            "db_diagnosis": """You are an expert Oracle DBA specializing in incident response.
You have access to runbooks, Oracle documentation, and historical incidents.
Analyze the provided error and context, then give:
1. Error Classification
2. Root Cause Analysis
3. Immediate Actions
4. Prevention Recommendations

Use the RETRIEVED CONTEXT to inform your analysis.""",

            "general": """You are an AI assistant for database administrators.
Use the provided context to answer questions accurately.
If the context doesn't contain relevant information, say so.""",

            "checkmk_correlation": """You are correlating CheckMK monitoring data with database events.
Identify patterns that might explain the database issue."""
        }
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        TODO: Replace with Ollama embedding API or sentence-transformers for production.
        """
        return generate_simple_embedding(text)
    
    def retrieve_context(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search Qdrant for relevant documents.
        """
        query_embedding = self.embed_text(query)
        results = self.vector_db.search(query_embedding, limit=limit)
        return results
    
    def format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant documents found in knowledge base."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get("source", "Unknown")
            content = doc.get("content", "")
            score = doc.get("score", 0)
            
            context_parts.append(f"""
--- Document {i} (Source: {source}, Relevance: {score:.2f}) ---
{content}
""")
        
        return "\n".join(context_parts)
    
    def diagnose_error(self, error_line: str, log_context: List[str], 
                       additional_info: Dict = None) -> Dict[str, Any]:
        """
        Full RAG diagnosis of a database error.
        
        Args:
            error_line: The specific error (e.g., "ORA-00600: internal error code")
            log_context: Preceding log lines for forensic context
            additional_info: Optional dict with DB name, metrics, etc.
            
        Returns:
            Dict with 'diagnosis', 'retrieved_docs', 'confidence'
        """
        # Step 1: Retrieve relevant knowledge
        search_query = f"{error_line} database error troubleshooting"
        retrieved_docs = self.retrieve_context(search_query, limit=3)
        formatted_context = self.format_context(retrieved_docs)
        
        # Step 2: Format log context
        log_text = "\n".join(log_context[-30:]) if log_context else "No log context provided."
        
        # Step 3: Build augmented prompt
        db_info = ""
        if additional_info:
            db_info = f"""
**Database Information:**
- Name: {additional_info.get('db_name', 'Unknown')}
- Engine: {additional_info.get('engine', 'Unknown')}
- Status: {additional_info.get('status', 'Unknown')}
"""
        
        augmented_prompt = f"""
**ERROR TO ANALYZE:**
{error_line}

{db_info}

**LOG CONTEXT (preceding {len(log_context)} lines):**
```
{log_text}
```

**RETRIEVED KNOWLEDGE BASE CONTEXT:**
{formatted_context}

Based on the error, log context, and retrieved documentation, provide your diagnosis:
"""
        
        # Step 4: Generate response
        response = self.llm.generate(
            prompt=augmented_prompt,
            system=self.system_prompts["db_diagnosis"]
        )
        
        if response.get("error"):
            return {
                "diagnosis": f"AI unavailable: {response['error']}",
                "retrieved_docs": retrieved_docs,
                "confidence": 0.0,
                "error": True
            }
        
        diagnosis_text = response.get("response", "No diagnosis generated")
        
        # Calculate confidence based on retrieval quality
        avg_score = sum(d.get("score", 0) for d in retrieved_docs) / max(len(retrieved_docs), 1)
        confidence = min(avg_score * 1.2, 1.0)  # Scale up slightly, cap at 1.0
        
        return {
            "diagnosis": diagnosis_text,
            "retrieved_docs": [{"source": d.get("source"), "content": d.get("content", "")[:200]} 
                              for d in retrieved_docs],
            "confidence": round(confidence, 2),
            "error": False
        }
    
    def answer_question(self, question: str) -> str:
        """
        General RAG Q&A for database-related questions.
        """
        retrieved = self.retrieve_context(question, limit=3)
        context = self.format_context(retrieved)
        
        prompt = f"""
**Question:** {question}

**Retrieved Context:**
{context}

Answer the question based on the context:
"""
        
        response = self.llm.generate(prompt, system=self.system_prompts["general"])
        return response.get("response", "Unable to generate answer")
    
    def index_document(self, content: str, source: str, doc_type: str = "runbook", 
                       metadata: Dict = None) -> bool:
        """
        Add a document to the knowledge base.
        
        Args:
            content: Document text
            source: Source identifier (e.g., "Oracle MOS", "Internal Runbook")
            doc_type: Type classification
            metadata: Additional metadata
            
        Returns:
            Success boolean
        """
        embedding = self.embed_text(content)
        
        doc = {
            "content": content,
            "source": source,
            "type": doc_type,
            "metadata": metadata or {}
        }
        
        return self.vector_db.upsert_documents([doc], [embedding])
    
    def seed_knowledge_base(self) -> int:
        """
        Seed the knowledge base with common Oracle error resolutions.
        Returns count of documents added.
        """
        seed_docs = [
            {
                "content": """ORA-00600: Internal Error Code
This is an internal Oracle error indicating a bug or corruption.
Actions:
1. Check alert log for additional details
2. Look for trace files in $ORACLE_BASE/diag/rdbms/<db>/<SID>/trace/
3. Search MOS for the specific ORA-00600 arguments
4. Consider opening an SR with Oracle Support
Prevention: Keep database patched, monitor for unusual activity""",
                "source": "Oracle KB",
                "type": "runbook",
                "error_codes": ["ORA-00600"]
            },
            {
                "content": """ORA-01555: Snapshot Too Old
Caused by:
- UNDO tablespace too small
- Long-running queries conflicting with DML
- UNDO_RETENTION too low
Resolution:
1. Increase UNDO tablespace size
2. Set UNDO_RETENTION higher (e.g., 3600 for 1 hour)
3. Consider optimizing long-running queries""",
                "source": "Oracle KB",
                "type": "runbook",
                "error_codes": ["ORA-01555"]
            },
            {
                "content": """ORA-04031: Unable to allocate shared memory
Shared pool fragmentation or undersized SGA.
Resolution:
1. Flush shared pool: ALTER SYSTEM FLUSH SHARED_POOL;
2. Increase SHARED_POOL_SIZE
3. Check for excessive literal SQL - use bind variables
4. Monitor with V$SHARED_POOL_ADVICE""",
                "source": "Oracle KB",
                "type": "runbook",
                "error_codes": ["ORA-04031"]
            },
            {
                "content": """DataGuard Lag Troubleshooting
If transport lag is high:
1. Check network connectivity between primary and standby
2. Verify LOG_ARCHIVE_DEST_n configuration
3. Check standby redo log sizes
4. Monitor V$DATAGUARD_STATS

If apply lag is high:
1. Check MRP process status
2. Look for gaps in archive logs
3. Verify PARALLEL_APPLY settings
4. Check for IO bottlenecks on standby""",
                "source": "DBA Playbook",
                "type": "runbook"
            },
            {
                "content": """RMAN Backup Failure Troubleshooting
Common causes:
1. Disk space full in backup destination
2. Channel allocation errors
3. Archive logs missing
4. FRA space exhausted

Diagnostic steps:
1. Check RMAN log for specific error
2. Verify backup destination accessibility
3. Query V$RMAN_BACKUP_JOB_DETAILS for history
4. Check V$RECOVERY_FILE_DEST for FRA usage""",
                "source": "DBA Playbook",
                "type": "runbook"
            }
        ]
        
        # Ensure collection exists
        self.vector_db.create_collection()
        
        count = 0
        for doc in seed_docs:
            embedding = self.embed_text(doc["content"])
            if self.vector_db.upsert_documents([doc], [embedding]):
                count += 1
        
        return count


# Test
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("🧠 Testing RAG Pipeline...")
    
    rag = RAGPipeline()
    
    # Check dependencies
    print("\n📡 Checking connections...")
    llm_ok = rag.llm.health_check()
    qdrant_ok = rag.vector_db.health_check()
    print(f"   Ollama: {'✅' if llm_ok else '❌'}")
    print(f"   Qdrant: {'✅' if qdrant_ok else '❌'}")
    
    if qdrant_ok:
        # Seed KB
        print("\n📚 Seeding Knowledge Base...")
        count = rag.seed_knowledge_base()
        print(f"   Added {count} documents")
    
    if llm_ok and qdrant_ok:
        # Test diagnosis
        print("\n🔍 Testing Error Diagnosis...")
        result = rag.diagnose_error(
            error_line="ORA-00600: internal error code, arguments: [kghstack1]",
            log_context=[
                "2026-01-05 14:30:00.000 INFO: Checkpoint started",
                "2026-01-05 14:30:05.000 INFO: Checkpoint completed",
                "2026-01-05 14:35:00.000 ERROR: ORA-00600: internal error code, arguments: [kghstack1]"
            ],
            additional_info={"db_name": "PROD1", "engine": "ORACLE"}
        )
        
        print(f"\n📋 Diagnosis Result:")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Retrieved Docs: {len(result['retrieved_docs'])}")
        print(f"\n   Diagnosis:\n{result['diagnosis'][:500]}...")
