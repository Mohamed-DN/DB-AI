import asyncio
import os
from dotenv import load_dotenv
from api_agents.workers.aiassistant.services.rag_service import RAGService

load_dotenv()

async def main():
    print("🚀 Initializing RAG Ingester...")
    rag = RAGService()
    
    doc_content = """
    # Oracle Error: ORA-00600 [12345]
    **Description:** Internal error 12345 relates to corrupt data blocks in table segment headers.
    **Resolution:** 
    1. Run `ANALYZE TABLE <table_name> VALIDATE STRUCTURE CASCADE;`
    2. Check alert.log for trace files.
    3. If block corruption is confirmed, restore from backup or use DBMS_REPAIR.
    """
    
    metadata = {
        "source": "Oracle Runbook 2024",
        "domain": "oracle",
        "error_code": "ORA-00600",
        "type": "runbook"
    }
    
    print(f"📥 Ingesting document: {metadata['error_code']}...")
    try:
        await rag.ingest_document(doc_content, metadata)
        print("✅ Ingestion successful!")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
