"""
Qdrant Vector DB Client - Semantic Search for Knowledge Base
Connects to Qdrant running in Docker at nexi-qdrant:6333
"""

import os
import json
import requests
from typing import Optional, Dict, List, Any
import hashlib

class QdrantClient:
    """Client for interacting with Qdrant Vector Database"""
    
    def __init__(self, host: str = None, collection: str = "nexi_knowledge_base"):
        self.host = host or os.getenv("QDRANT_HOST", "http://localhost:6333")
        self.collection = collection
        self.embedding_dim = 384  # Default for sentence-transformers/all-MiniLM-L6-v2
        
    def health_check(self) -> bool:
        """Check if Qdrant is reachable"""
        try:
            response = requests.get(f"{self.host}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_collection(self, name: str = None, vector_size: int = None) -> bool:
        """Create a new collection if it doesn't exist"""
        collection_name = name or self.collection
        vector_size = vector_size or self.embedding_dim
        
        url = f"{self.host}/collections/{collection_name}"
        
        # Check if exists
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True  # Already exists
        except:
            pass
        
        # Create
        payload = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            }
        }
        
        try:
            response = requests.put(url, json=payload, timeout=10)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def upsert_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """
        Insert or update documents with their embeddings.
        
        Args:
            documents: List of {"id": str, "content": str, "metadata": {...}}
            embeddings: List of embedding vectors corresponding to documents
            
        Returns:
            Success boolean
        """
        url = f"{self.host}/collections/{self.collection}/points"
        
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Generate stable ID from content hash if not provided
            doc_id = doc.get("id") or hashlib.md5(doc["content"].encode()).hexdigest()[:16]
            
            points.append({
                "id": abs(hash(doc_id)) % (10**9),  # Qdrant needs numeric ID
                "vector": embedding,
                "payload": {
                    "content": doc["content"],
                    "source": doc.get("source", "unknown"),
                    "type": doc.get("type", "document"),
                    **doc.get("metadata", {})
                }
            })
        
        payload = {"points": points}
        
        try:
            response = requests.put(url, json=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return False
    
    def search(self, query_vector: List[float], limit: int = 5, 
               filter_conditions: Dict = None) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query_vector: The embedding of the search query
            limit: Max number of results
            filter_conditions: Optional Qdrant filter
            
        Returns:
            List of matching documents with scores
        """
        url = f"{self.host}/collections/{self.collection}/points/search"
        
        payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True
        }
        
        if filter_conditions:
            payload["filter"] = filter_conditions
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            results = response.json().get("result", [])
            return [
                {
                    "score": r["score"],
                    "content": r["payload"].get("content"),
                    "source": r["payload"].get("source"),
                    "type": r["payload"].get("type"),
                    "metadata": {k: v for k, v in r["payload"].items() 
                                if k not in ["content", "source", "type"]}
                }
                for r in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_by_error_code(self, error_code: str, limit: int = 3) -> List[Dict]:
        """
        Specialized search for database error codes.
        Searches with filter for error-related documents.
        
        Note: Requires pre-computed embedding. For now, returns based on payload filter.
        """
        url = f"{self.host}/collections/{self.collection}/points/scroll"
        
        # Simple payload-based search (not vector search)
        payload = {
            "limit": limit,
            "with_payload": True,
            "filter": {
                "should": [
                    {"key": "content", "match": {"text": error_code}},
                    {"key": "error_codes", "match": {"any": [error_code]}}
                ]
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                results = response.json().get("result", {}).get("points", [])
                return [r["payload"] for r in results]
            return []
        except:
            return []
    
    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        try:
            response = requests.get(f"{self.host}/collections/{self.collection}", timeout=5)
            if response.status_code == 200:
                return response.json().get("result", {})
            return {}
        except:
            return {}
    
    def delete_collection(self, name: str = None) -> bool:
        """Delete a collection"""
        collection_name = name or self.collection
        try:
            response = requests.delete(f"{self.host}/collections/{collection_name}", timeout=10)
            return response.status_code == 200
        except:
            return False


# Utility: Simple embedding generator (placeholder - real impl needs sentence-transformers)
def generate_simple_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Generate a simple hash-based pseudo-embedding.
    PRODUCTION: Replace with sentence-transformers or Ollama embeddings.
    """
    import hashlib
    # Create deterministic pseudo-random vector from text hash
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    # Convert hex to floats
    embedding = []
    for i in range(0, min(len(text_hash), dim * 2), 2):
        val = int(text_hash[i:i+2], 16) / 255.0 - 0.5  # Normalize to [-0.5, 0.5]
        embedding.append(val)
    # Pad if needed
    while len(embedding) < dim:
        embedding.append(0.0)
    return embedding[:dim]


# Quick test
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    client = QdrantClient()
    
    print("🔍 Testing Qdrant Connection...")
    if client.health_check():
        print("✅ Qdrant is reachable")
        
        # Create collection
        print("\n📦 Creating collection...")
        if client.create_collection():
            print(f"   Collection '{client.collection}' ready")
            
            # Insert test document
            print("\n📄 Inserting test document...")
            test_docs = [
                {
                    "content": "ORA-00600 is an internal Oracle error. Check the trace file for details.",
                    "source": "Oracle MOS",
                    "type": "runbook",
                    "error_codes": ["ORA-00600"]
                }
            ]
            test_embeddings = [generate_simple_embedding(test_docs[0]["content"])]
            
            if client.upsert_documents(test_docs, test_embeddings):
                print("   ✅ Document inserted")
                
            # Get info
            info = client.get_collection_info()
            print(f"   Collection points: {info.get('points_count', 0)}")
    else:
        print("❌ Cannot connect to Qdrant")
