import os
import sys
import shutil
from fastapi.testclient import TestClient

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
import config

client = TestClient(app)

def create_sample_pdf(filename: str):
    import fitz
    print(f"\n--- Creating sample PDF: {filename} ---")
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Hello world from Enterprise RAG! This is page 1 content.\n"
                                "Retrieval Augmented Generation (RAG) is a technique that combines retrieval "
                                "mechanisms with generative LLMs to answer questions accurately using external data.\n"
                                "By retrieving relevant chunks from the database, the model avoids hallucinations.")
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 50), "This is page 2 content.\n"
                                "The Groq API is used as the LLM interface, specifically employing llama3-8b-8192.\n"
                                "Sentence-transformers model all-MiniLM-L6-v2 computes dense vector representations "
                                "of the document chunks, which are stored in ChromaDB.")
    
    doc.save(filename)
    doc.close()
    print(f"Sample PDF created successfully.")

def run_tests():
    # Setup test file
    test_pdf_name = "api_test_doc.pdf"
    test_pdf_path = os.path.join(config.UPLOAD_DIR, test_pdf_name)
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    collection_name = "api_test_doc"
    
    # Pre-test cleanup: ensure collection does not already exist from a previous failed run
    try:
        existing = client.get("/documents").json().get("documents", [])
        if any(doc["collection_name"] == collection_name for doc in existing):
            print(f"Pre-test cleanup: deleting existing '{collection_name}' collection...")
            client.delete(f"/documents/{collection_name}")
    except Exception as e:
        print(f"Warning during pre-test cleanup: {e}")

    # Generate sample PDF after cleanup
    create_sample_pdf(test_pdf_path)

    
    try:
        # 1. Test Health Endpoint
        print("\n=== Testing GET /health ===")
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, "Health check failed"
        print(f"Health Response: {health_resp.json()}")
        
        # 2. Test Upload Endpoint
        print("\n=== Testing POST /upload ===")
        with open(test_pdf_path, "rb") as f:
            upload_resp = client.post("/upload", files={"file": (test_pdf_name, f, "application/pdf")})
            
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        data = upload_resp.json()
        print(f"Upload Response: {data}")
        print(f"Process Time Header: {upload_resp.headers.get('X-Process-Time')} ms")
        assert data["success"] is True
        assert data["collection_name"] == collection_name
        assert data["total_pages"] == 2
        
        # 3. Test Conflict Upload
        print("\n=== Testing POST /upload (Conflict) ===")
        with open(test_pdf_path, "rb") as f:
            conflict_resp = client.post("/upload", files={"file": (test_pdf_name, f, "application/pdf")})
        assert conflict_resp.status_code == 409, f"Expected 409, got: {conflict_resp.status_code}"
        print(f"Conflict Response: {conflict_resp.json()}")

        # 4. Test Get Documents
        print("\n=== Testing GET /documents ===")
        docs_resp = client.get("/documents")
        assert docs_resp.status_code == 200
        docs_data = docs_resp.json()
        print(f"Documents: {docs_data}")
        assert docs_data["total"] >= 1
        
        # 5. Test Query Endpoint
        print("\n=== Testing POST /query ===")
        query_payload = {
            "question": "What is RAG and what models are used for embeddings?",
            "collection_name": collection_name,
            "n_results": 2
        }
        query_resp = client.post("/query", json=query_payload)
        assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"
        query_data = query_resp.json()
        print(f"Answer: {query_data['answer']}")
        print(f"Pages Referenced: {query_data['pages_referenced']}")
        print(f"Sources: {query_data['sources']}")
        print(f"Process Time Header: {query_resp.headers.get('X-Process-Time')} ms")
        assert len(query_data["sources"]) > 0
        assert query_data["sources"][0]["relevance_score"] > 0.0

        # 6. Test Delete Endpoint
        print("\n=== Testing DELETE /documents/{collection_name} ===")
        del_resp = client.delete(f"/documents/{collection_name}")
        assert del_resp.status_code == 200
        print(f"Delete Response: {del_resp.json()}")
        
        # Confirm deleted in /documents
        docs_resp_after = client.get("/documents")
        col_names = [d["collection_name"] for d in docs_resp_after.json()["documents"]]
        assert collection_name not in col_names, "Collection should be deleted"
        
        # Confirm PDF file is deleted from uploads/
        assert not os.path.exists(test_pdf_path), "Physical PDF file should be deleted"
        
        print("\nALL API ENDPOINT TESTS PASSED SUCCESSFULLY!")
        
    finally:
        # Clean up files if they exist
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print("Cleaned up test PDF.")

if __name__ == "__main__":
    print("Starting API integration tests using FastAPI TestClient...")
    try:
        run_tests()
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)
