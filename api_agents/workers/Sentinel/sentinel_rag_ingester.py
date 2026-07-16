"""
Sentinel RAG Ingester - Knowledge Base Builder

Scans the repository for SQL scripts, stored procedures, and operational
documentation. Indexes content into Qdrant vector database for semantic
search during alert verification and remediation.

Part of the Sentinel Engine Multi-Agent System.
"""
import os
import sys
import re
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Add root path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

logger = logging.getLogger("SentinelRAGIngester")


@dataclass
class DocumentChunk:
    """A chunk of text ready for embedding and indexing"""
    id: str
    text: str
    source_file: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to Qdrant payload format"""
        return {
            "text": self.text,
            "source": self.source_file,
            "chunk_index": self.chunk_index,
            "indexed_at": datetime.utcnow().isoformat(),
            **self.metadata
        }


class TextChunker:
    """Utility for chunking text into overlapping segments"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for period, newline, or semicolon near the end
                for sep in ['. ', '\n\n', ';\n', '\n', '; ']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + self.chunk_size // 2:
                        end = last_sep + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap
            if start >= len(text):
                break
        
        return chunks


class SQLAnalyzer:
    """Analyzes SQL scripts to extract metadata"""
    
    # Patterns for extracting SQL metadata
    PATTERNS = {
        "procedure_name": re.compile(r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|FUNCTION)\s+(\w+)', re.IGNORECASE),
        "table_refs": re.compile(r'(?:FROM|JOIN|INTO|UPDATE)\s+(\w+)', re.IGNORECASE),
        "oracle_hints": re.compile(r'/\*\+\s*([^*]+)\s*\*/', re.IGNORECASE),
        "comments": re.compile(r'--\s*(.+)$|/\*([^*]|\*(?!/))*\*/', re.MULTILINE),
        "keywords": re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE)\b', re.IGNORECASE),
    }
    
    def analyze(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from SQL content"""
        metadata = {
            "file_type": "sql",
            "filename": filename
        }
        
        # Extract procedure/function names
        procs = self.PATTERNS["procedure_name"].findall(content)
        if procs:
            metadata["procedures"] = procs
        
        # Extract table references
        tables = list(set(self.PATTERNS["table_refs"].findall(content)))
        if tables:
            metadata["tables"] = tables[:10]  # Limit to first 10
        
        # Count SQL operations
        keywords = self.PATTERNS["keywords"].findall(content)
        metadata["operations"] = list(set(k.upper() for k in keywords))
        
        # Check for Oracle-specific features
        if "/*+" in content:
            metadata["has_hints"] = True
        if "DBMS_" in content.upper():
            metadata["uses_dbms_packages"] = True
        if "EXECUTE IMMEDIATE" in content.upper():
            metadata["uses_dynamic_sql"] = True
        
        # Detect script purpose from comments
        first_comment = re.search(r'^--\s*(.+)$', content, re.MULTILINE)
        if first_comment:
            metadata["description"] = first_comment.group(1)[:200]
        
        return metadata


class SentinelRAGIngester:
    """
    Scans repository for SQL scripts and documentation,
    indexes into Qdrant for semantic search during alert handling.
    """
    
    # File patterns to scan
    SCAN_PATTERNS = [
        "*.sql",
        "*.pls",
        "*.plsql",
        "*.pck",
        "*.pkb",
        "*.pks",
        "*.md",
        "*.txt",
        "*.py"  # Python scripts may contain operational procedures
    ]
    
    # Directories to scan
    DEFAULT_SCAN_DIRS = [
        "Metriche_oem",
        "ops/scripts",
        "scripts",
        "sql",
        "procedures",
        "docs"
    ]
    
    # Directories to skip
    SKIP_DIRS = {
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "env"
    }
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        collection_name: str = "m-dn_sop_knowledge",
        repo_root: Optional[str] = None
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:7333")
        self.collection_name = collection_name
        self.repo_root = repo_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../../..')
        )
        
        self.chunker = TextChunker(chunk_size=1000, overlap=200)
        self.sql_analyzer = SQLAnalyzer()
        
        # Initialize Qdrant client
        self.qdrant = None
        self._init_qdrant()
    
    def _init_qdrant(self):
        """Initialize Qdrant client and ensure collection exists"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.qdrant = QdrantClient(url=self.qdrant_url)
            
            # Check if collection exists, create if not
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection with appropriate vector size
                # Using 384 dimensions (common for small embedding models)
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except ImportError:
            logger.error("qdrant-client not installed. Run: pip install qdrant-client")
            self.qdrant = None
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self.qdrant = None
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Uses Ollama embeddings if available, otherwise returns placeholder.
        """
        try:
            import httpx
            
            # Try Ollama embeddings
            resp = httpx.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text[:8000]  # Limit text length
                },
                timeout=30.0
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding", [0.0] * 384)
                
        except Exception as e:
            logger.debug(f"Ollama embedding failed, using fallback: {e}")
        
        # Fallback: simple TF-IDF-like embedding (placeholder)
        # In production, use sentence-transformers or similar
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> i) % 256 / 256.0 for i in range(384)]
    
    def _generate_chunk_id(self, source_file: str, chunk_index: int) -> str:
        """Generate unique ID for a chunk"""
        content = f"{source_file}:{chunk_index}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def scan_directory(self, directory: str) -> List[Path]:
        """Scan directory for files matching patterns"""
        files = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return files
        
        for pattern in self.SCAN_PATTERNS:
            for file_path in dir_path.rglob(pattern):
                # Skip excluded directories
                if any(skip in file_path.parts for skip in self.SKIP_DIRS):
                    continue
                files.append(file_path)
        
        return files
    
    def process_file(self, file_path: Path) -> List[DocumentChunk]:
        """Process a single file into chunks"""
        chunks = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            if not content.strip():
                return chunks
            
            # Determine file type and extract metadata
            suffix = file_path.suffix.lower()
            rel_path = str(file_path.relative_to(self.repo_root) if file_path.is_relative_to(self.repo_root) else file_path)
            
            if suffix in ['.sql', '.pls', '.plsql', '.pck', '.pkb', '.pks']:
                metadata = self.sql_analyzer.analyze(content, file_path.name)
            else:
                metadata = {
                    "file_type": suffix[1:] if suffix else "unknown",
                    "filename": file_path.name
                }
            
            # Chunk the content
            text_chunks = self.chunker.chunk_text(content)
            
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = self._generate_chunk_id(rel_path, i)
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    text=chunk_text,
                    source_file=rel_path,
                    chunk_index=i,
                    metadata=metadata
                ))
            
            logger.debug(f"Processed {file_path.name}: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        
        return chunks
    
    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Index chunks into Qdrant"""
        if not self.qdrant:
            logger.error("Qdrant client not available")
            return 0
        
        if not chunks:
            return 0
        
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for chunk in chunks:
                embedding = self._generate_embedding(chunk.text)
                points.append(PointStruct(
                    id=chunk.id,
                    vector=embedding,
                    payload=chunk.to_payload()
                ))
            
            # Batch upsert
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return len(points)
            
        except Exception as e:
            logger.error(f"Failed to index chunks: {e}")
            return 0
    
    def run_ingestion(self, directories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run full ingestion process.
        
        Args:
            directories: List of directories to scan (relative to repo root)
            
        Returns:
            Summary of ingestion results
        """
        if directories is None:
            directories = self.DEFAULT_SCAN_DIRS
        
        results = {
            "directories_scanned": 0,
            "files_found": 0,
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_indexed": 0,
            "errors": []
        }
        
        all_chunks = []
        
        for dir_name in directories:
            dir_path = os.path.join(self.repo_root, dir_name)
            
            if not os.path.exists(dir_path):
                logger.debug(f"Directory not found: {dir_path}")
                continue
            
            results["directories_scanned"] += 1
            
            files = self.scan_directory(dir_path)
            results["files_found"] += len(files)
            
            for file_path in files:
                try:
                    chunks = self.process_file(file_path)
                    all_chunks.extend(chunks)
                    results["files_processed"] += 1
                    results["chunks_created"] += len(chunks)
                except Exception as e:
                    results["errors"].append(f"{file_path}: {str(e)}")
        
        # Index all chunks
        if all_chunks:
            indexed = self.index_chunks(all_chunks)
            results["chunks_indexed"] = indexed
        
        logger.info(
            f"📚 RAG Ingestion complete: {results['files_processed']} files, "
            f"{results['chunks_indexed']} chunks indexed"
        )
        
        return results
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching documents with scores
        """
        if not self.qdrant:
            return []
        
        try:
            embedding = self._generate_embedding(query)
            
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit
            )
            
            return [
                {
                    "text": r.payload.get("text", ""),
                    "source": r.payload.get("source", ""),
                    "score": r.score,
                    "metadata": {k: v for k, v in r.payload.items() if k not in ["text", "source"]}
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Sentinel RAG Ingester")
    parser.add_argument("--ingest", action="store_true", help="Run ingestion")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--dirs", nargs="+", help="Directories to scan")
    args = parser.parse_args()
    
    ingester = SentinelRAGIngester()
    
    if args.ingest:
        results = ingester.run_ingestion(args.dirs)
        print("\n📚 Ingestion Results:")
        for k, v in results.items():
            print(f"  {k}: {v}")
    
    if args.search:
        results = ingester.search(args.search)
        print(f"\n🔍 Search Results for '{args.search}':")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r['score']:.2f}] {r['source']}")
            print(f"   {r['text'][:200]}...")
