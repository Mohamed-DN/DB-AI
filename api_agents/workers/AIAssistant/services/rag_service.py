"""
RAG Service with Domain Chunking Support
Interacts with Qdrant (v2 compatible) and supports domain filtering.
"""
import os
import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # Determine ports - try environment first, then logic for V2/V1
        self.qdrant_host = os.getenv("QDRANT_HOST", "http://localhost")
        # Simple heuristic or env var for port. Defaulting to 6333 (V1) but config should handle V2 (7333)
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333)) 
        
        self.collection_name = os.getenv("QDRANT_COLLECTION", "nexi_knowledge")
        
        try:
            # Handle if host already has port (e.g. from env var)
            if ":" in self.qdrant_host.replace("http://", "").replace("https://", ""):
                 self.client = QdrantClient(url=self.qdrant_host)
            else:
                 self.client = QdrantClient(url=f"{self.qdrant_host}:{self.qdrant_port}")
            # Embeddings model - must match what stored the data
            self.embeddings = OllamaEmbeddings(
                model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            )
        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}")
            self.client = None

    async def search(self, query: str, domain: Optional[str] = None, limit: int = 3) -> List[Dict]:
        """
        Search for relevant chunks, optionally filtered by domain (e.g., 'oracle', 'postgres').
        """
        if not self.client:
            return []

        try:
            vector = self.embeddings.embed_query(query)
            
            # Construct Filter if domain is present
            query_filter = None
            if domain:
                from qdrant_client.http import models
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.domain",
                            match=models.MatchValue(value=domain)
                        )
                    ]
                )

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter,
                limit=limit
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload.get("page_content", ""),
                    "metadata": hit.payload.get("metadata", {}),
                    "score": hit.score
                })
                
            return results

        except Exception as e:
            logger.error(f"RAG Search failed: {e}")
            return []

    async def ingest_document(self, content: str, metadata: Dict):
        """Simple ingestion method for runbooks/SOPs"""
        if not self.client:
            return
            
        try:
            validation_vector = self.embeddings.embed_query("test") # validation
            vector = self.embeddings.embed_query(content)
            
            from qdrant_client.http import models
            import uuid
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "page_content": content,
                            "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
