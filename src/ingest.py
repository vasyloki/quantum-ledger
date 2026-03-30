import os
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('BAAI/bge-small-en-v1.5') 
converter = DocumentConverter()
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

COLLECTION_NAME = "financial_intel"

def run_ingestion():
    data_root = "./data"
    
    # os.walk travels through every subfolder for you
    for root, dirs, files in os.walk(data_root):
        for file_name in files:
            if file_name.endswith((".pdf", ".html")):
                file_path = os.path.join(root, file_name)
                # Capture the subfolder name (e.g., 'nvidia') as a metadata tag
                company_name = os.path.basename(root) 
                
                print(f"🚀 Ingesting [{company_name}]: {file_name}...")
                
                try:
                    result = converter.convert(file_path)
                    text_content = result.document.export_to_markdown()

                    chunks = [text_content[i:i + 1000] for i in range(0, len(text_content), 900)]
                    
                    points = []
                    for i, chunk in enumerate(chunks):
                        vector = model.encode(chunk).tolist()
                        point_id = hash(f"{file_name}_{i}") & 0xFFFFFFFFFFFFFFFF
                        
                        points.append(models.PointStruct(
                            id=point_id,
                            vector={"text-dense": vector},
                            payload={
                                "page_content": chunk,
                                "metadata": {
                                    "source": file_name,
                                    "company": company_name, # Critical for filtering later!
                                    "chunk_index": i
                                }
                            }
                        ))
                    
                    client.upsert(collection_name=COLLECTION_NAME, points=points)
                    print(f"✅ Uploaded {len(points)} chunks from {file_name}")
                except Exception as e:
                    print(f"⚠️ Failed to process {file_name}: {e}")

if __name__ == "__main__":
    run_ingestion()