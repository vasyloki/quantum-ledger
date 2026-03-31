import os
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker  # Added for 2.x API
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

# Configuration
COLLECTION_NAME = "financial_intel"
DATA_ROOT = "./data"

# Initialize Models and Clients
model = SentenceTransformer('BAAI/bge-small-en-v1.5') 
converter = DocumentConverter()
chunker = HybridChunker() # Initialize the separate chunker object
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

def run_ingestion():
    if not os.path.exists(DATA_ROOT):
        print(f"Error: Data directory {DATA_ROOT} not found.")
        return

    for root, dirs, files in os.walk(DATA_ROOT):
        for file_name in files:
            if file_name.endswith((".pdf", ".html")):
                file_path = os.path.join(root, file_name)
                company_name = os.path.basename(root).lower() 
                
                print(f"🚀 Processing [{company_name}]: {file_name}...")
                
                try:
                    # 1. Structural Conversion
                    # .document gets the DoclingDocument object the chunker needs
                    result = converter.convert(file_path).document
                    
                    points = []
                    
                    # 2. Layout-Aware Chunking (Corrected 2.x Syntax)
                    # We pass the doc to the chunker's .chunk() method
                    doc_chunks = chunker.chunk(result)
                    
                    for i, chunk in enumerate(doc_chunks):
                        # Use contextualize() for better retrieval (includes headings/metadata)
                        text_content = chunker.contextualize(chunk)
                        
                        if len(text_content) < 40:
                            continue

                        # 3. Embedding Generation
                        vector = model.encode(text_content).tolist()
                        point_id = hash(f"{file_name}_{i}") & 0xFFFFFFFFFFFFFFFF
                        
                        # 4. Payload Construction
                        points.append(models.PointStruct(
                            id=point_id,
                            vector={"text-dense": vector},
                            payload={
                                "page_content": text_content,
                                "metadata": {
                                    "source": file_name,
                                    "company": company_name, 
                                    "chunk_index": i
                                }
                            }
                        ))
                    
                    # 5. Batch Upsert
                    if points:
                        client.upsert(collection_name=COLLECTION_NAME, points=points)
                        print(f"✅ Uploaded {len(points)} semantic chunks from {file_name}")
                    
                except Exception as e:
                    print(f"⚠️ Failed to process {file_name}: {e}")

if __name__ == "__main__":
    run_ingestion()