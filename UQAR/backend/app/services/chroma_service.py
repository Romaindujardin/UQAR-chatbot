import logging
from typing import List, Dict, Optional, Any

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    logging.warning(f"ChromaDB not available: {e}")
    CHROMADB_AVAILABLE = False

from ..core.config import settings

logger = logging.getLogger(__name__)


class ChromaService:
    """Service pour interagir avec ChromaDB"""
    
    def __init__(self):
        self.chroma_client = None
        
        if CHROMADB_AVAILABLE:
            try:
                # Try HTTP client first
                self.chroma_client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
                logger.info("ChromaDB initialized as HttpClient")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB HttpClient: {e}")
                # Fallback to PersistentClient
                try:
                    self.chroma_client = chromadb.PersistentClient(
                        path=settings.CHROMA_PERSIST_DIRECTORY
                    )
                    logger.info("ChromaDB initialized as PersistentClient")
                except Exception as e2:
                    logger.error(f"Failed to initialize ChromaDB: {e2}")
                    self.chroma_client = None
        else:
            logger.warning("ChromaDB is not available")
            
    async def query_similar_chunks(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query similar chunks from a ChromaDB collection"""
        
        if not self.chroma_client:
            logger.warning("ChromaDB client not available")
            return []
            
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # Build query parameters
            query_params = {
                "query_texts": [query_text],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add metadata filter if provided
            if metadata_filter:
                query_params["where"] = metadata_filter
                
            results = collection.query(**query_params)
            
            # Format results
            chunks = []
            if results and "documents" in results and results["documents"]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if "metadatas" in results else [{}] * len(documents)
                distances = results["distances"][0] if "distances" in results else [1.0] * len(documents)
                
                for doc, meta, dist in zip(documents, metadatas, distances):
                    chunks.append({
                        "text": doc,
                        "metadata": meta,
                        "distance": dist
                    })
                    
            return chunks
            
        except Exception as e:
            logger.error(f"Error querying ChromaDB collection {collection_name}: {e}")
            return []
            
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a ChromaDB collection"""
        
        if not self.chroma_client:
            return None
            
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None 