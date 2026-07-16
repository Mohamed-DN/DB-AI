
import qdrant_client
from qdrant_client.http import models

def init_qdrant():
    print("🔌 Connecting to Qdrant...")
    client = qdrant_client.QdrantClient("http://localhost:6333")
    
    collection_name = "m-dn_knowledge"
    
    try:
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if exists:
            print(f"✅ Collection '{collection_name}' already exists.")
        else:
            print(f"⚠️ Collection '{collection_name}' not found. Creating...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
            print(f"✅ Collection '{collection_name}' created successfully.")
            
    except Exception as e:
        print(f"❌ Failed to initialize Qdrant: {e}")

if __name__ == "__main__":
    init_qdrant()
