"""
Script pour vérifier le contenu de ChromaDB pour les sections
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
import logging

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except:
    CHROMADB_AVAILABLE = False

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"

def check_chromadb_content():
    """Vérifier le contenu de ChromaDB pour chaque section"""
    
    # Get sections from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.name, s.chroma_collection_name, COUNT(d.id) as doc_count
        FROM sections s
        LEFT JOIN documents d ON s.id = d.section_id
        GROUP BY s.id, s.name, s.chroma_collection_name
    """)
    
    sections = cursor.fetchall()
    logger.info(f"Found {len(sections)} sections")
    
    if CHROMADB_AVAILABLE:
        try:
            # Initialize ChromaDB client
            chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            logger.info("ChromaDB client initialized")
            
            for section_id, section_name, collection_name, doc_count in sections:
                logger.info(f"\nSection {section_id}: {section_name}")
                logger.info(f"  Documents in DB: {doc_count}")
                logger.info(f"  Collection name: {collection_name}")
                
                if collection_name:
                    try:
                        collection = chroma_client.get_collection(name=collection_name)
                        count = collection.count()
                        logger.info(f"  Chunks in ChromaDB: {count}")
                        
                        # Get a sample
                        if count > 0:
                            sample = collection.peek(limit=1)
                            if sample and sample.get('documents'):
                                logger.info(f"  Sample content (first 200 chars): {sample['documents'][0][:200]}...")
                                if sample.get('metadatas'):
                                    logger.info(f"  Sample metadata: {sample['metadatas'][0]}")
                    except Exception as e:
                        logger.error(f"  Error accessing collection {collection_name}: {e}")
                else:
                    logger.warning("  No collection name set for this section")
                    
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            try:
                # Try PersistentClient
                chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
                logger.info("Using PersistentClient instead")
                
                # List all collections
                collections = chroma_client.list_collections()
                logger.info(f"Available collections: {[c.name for c in collections]}")
                
            except Exception as e2:
                logger.error(f"Failed with PersistentClient too: {e2}")
    else:
        logger.error("ChromaDB not available")
    
    conn.close()

if __name__ == "__main__":
    check_chromadb_content() 