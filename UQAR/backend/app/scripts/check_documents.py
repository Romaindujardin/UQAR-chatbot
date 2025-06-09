"""
Script pour vérifier l'état des documents
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/home/dujr0001/UQAR_GIT/apptainer_data/uqar.db"

def check_documents():
    """Vérifier l'état des documents"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get sections with documents
        cursor.execute("""
            SELECT s.id, s.name, COUNT(d.id) as doc_count
            FROM sections s
            LEFT JOIN documents d ON s.id = d.section_id
            GROUP BY s.id, s.name
            HAVING doc_count > 0
        """)
        
        sections = cursor.fetchall()
        logger.info(f"Found {len(sections)} sections with documents")
        
        for section_id, section_name, doc_count in sections:
            logger.info(f"\nSection {section_id}: {section_name} ({doc_count} documents)")
            
            # Get documents for this section
            cursor.execute("""
                SELECT id, original_filename, status, is_vectorized, 
                       text_length, LENGTH(extracted_text) as actual_text_length
                FROM documents
                WHERE section_id = ?
            """, (section_id,))
            
            documents = cursor.fetchall()
            
            for doc in documents:
                doc_id, filename, status, is_vectorized, text_length, actual_text_length = doc
                logger.info(f"  Document {doc_id}: {filename}")
                logger.info(f"    Status: {status}, Vectorized: {is_vectorized}")
                logger.info(f"    Text length (stored): {text_length}, Actual: {actual_text_length}")
                
                # Get a sample of the extracted text
                cursor.execute("""
                    SELECT SUBSTR(extracted_text, 1, 200) as sample
                    FROM documents
                    WHERE id = ?
                """, (doc_id,))
                
                sample = cursor.fetchone()
                if sample and sample[0]:
                    logger.info(f"    Text sample: {sample[0][:100]}...")
                else:
                    logger.info(f"    No extracted text found!")
                    
    except Exception as e:
        logger.error(f"Error checking documents: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_documents() 