import os
import sys
import time
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Ensure the backend directory is in the sys.path so services package can be imported directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from schemas import (
    HealthResponse,
    UploadResponse,
    DocumentsResponse,
    DocumentItem,
    StatsResponse,
    QueryRequest,
    QueryResponse,
    SourceItem,
    DeleteResponse
)

# Import and initialize services on startup
print("[Main] Initializing service layers...")
from services import pdf_service, embedding_service, vector_store_service, llm_service
print("[Main] All services initialized successfully.")

app = FastAPI(
    title="Enterprise RAG Knowledge Assistant API",
    description="Backend API for document ingestion, storage, and retrieval-augmented generation.",
    version="1.0.0"
)

# Configure CORS to allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Check the health of the API and its connection to external services.
    """
    chromadb_status = "disconnected"
    try:
        # ChromaDB heartbeat returns an integer timestamp if working
        if vector_store_service.client.heartbeat() is not None:
            chromadb_status = "connected"
    except Exception as e:
        print(f"[Health] ChromaDB check failed: {e}")
        
    embedding_status = "not loaded"
    if hasattr(embedding_service, 'model') and embedding_service.model is not None:
        embedding_status = "loaded"
        
    groq_status = "not configured"
    if config.GROQ_API_KEY:
        groq_status = "configured"
        
    return HealthResponse(
        status="ok",
        chromadb=chromadb_status,
        embedding_model=embedding_status,
        groq=groq_status
    )

@app.post("/upload", response_model=UploadResponse)
def upload_file(response: Response, file: UploadFile = File(...)):
    """
    Accepts a PDF document upload, parses it, chunks it, embeds it, and stores it in ChromaDB.
    """
    start_time = time.time()
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Derive collection name: remove extension and replace spaces with underscores
    base_name, _ = os.path.splitext(file.filename)
    collection_name_raw = base_name.replace(" ", "_")
    sanitized_collection = vector_store_service.sanitize_collection_name(collection_name_raw)
    
    # Check if collection already exists
    try:
        existing_collections = vector_store_service.get_all_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check existing documents: {e}")
        
    if sanitized_collection in existing_collections:
        raise HTTPException(status_code=409, detail="Document already uploaded. Delete it first to re-upload.")
        
    # Save the file physically in uploads/ directory
    file_path = os.path.join(config.UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file locally: {e}")
        
    # Run the ingestion and indexing pipeline
    try:
        # Extract text
        pages = pdf_service.extract_text_from_pdf(file_path)
        total_pages = len(pages)
        
        # Chunk text
        chunks = pdf_service.chunk_text(pages)
        total_chunks = len(chunks)
        
        if total_chunks == 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail="No readable text found in the PDF.")
            
        # Get embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.get_embeddings(texts)
        
        # Store in ChromaDB
        vector_store_service.add_document(chunks, embeddings, sanitized_collection)
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up local file in case of processing failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error during PDF processing pipeline: {e}")
        
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}"
    
    return UploadResponse(
        success=True,
        file_name=file.filename,
        collection_name=sanitized_collection,
        total_pages=total_pages,
        total_chunks=total_chunks,
        message="Document processed and indexed successfully"
    )

@app.get("/documents", response_model=DocumentsResponse)
def get_documents():
    """
    Retrieves all indexed document collections and matches them against uploads.
    """
    try:
        collections = vector_store_service.get_all_collections()
        document_items = []
        
        for col_name in collections:
            file_name = f"{col_name}.pdf"  # Fallback guess
            file_exists = False
            
            # Fetch the actual original file name from the collection metadata if possible
            try:
                collection = vector_store_service.client.get_collection(name=col_name)
                peek = collection.get(limit=1)
                if peek and peek.get("metadatas") and len(peek["metadatas"]) > 0:
                    file_name = peek["metadatas"][0].get("file_name", file_name)
            except Exception as e:
                print(f"[Main] Warning: Could not retrieve filename for collection {col_name}: {e}")
                
            file_path = os.path.join(config.UPLOAD_DIR, file_name)
            if os.path.exists(file_path):
                file_exists = True
                
            document_items.append(
                DocumentItem(
                    collection_name=col_name,
                    file_name=file_name,
                    file_exists=file_exists
                )
            )
            
        return DocumentsResponse(
            documents=document_items,
            total=len(document_items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents list: {e}")

@app.delete("/documents/{collection_name}", response_model=DeleteResponse)
def delete_document(collection_name: str):
    """
    Deletes the ChromaDB collection and removes the corresponding PDF file from storage.
    """
    sanitized_collection = vector_store_service.sanitize_collection_name(collection_name)
    
    try:
        collections = vector_store_service.get_all_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collections: {e}")
        
    if sanitized_collection not in collections:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    # Get original filename before deletion
    file_name = None
    try:
        collection = vector_store_service.client.get_collection(name=sanitized_collection)
        peek = collection.get(limit=1)
        if peek and peek.get("metadatas") and len(peek["metadatas"]) > 0:
            file_name = peek["metadatas"][0].get("file_name")
    except Exception as e:
        print(f"[Main] Warning: Could not retrieve filename before deletion for {sanitized_collection}: {e}")
        
    # Delete from ChromaDB
    try:
        vector_store_service.delete_collection(sanitized_collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete ChromaDB collection: {e}")
        
    # Delete file from local uploads folder
    if file_name:
        file_path = os.path.join(config.UPLOAD_DIR, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[Main] Warning: Failed to delete physical file {file_path}: {e}")
                
    return DeleteResponse(
        success=True,
        message="Document deleted successfully"
    )

@app.get("/documents/{collection_name}/stats", response_model=StatsResponse)
def get_document_stats(collection_name: str):
    """
    Returns the total number of chunks and filename indexed for a collection.
    """
    sanitized_collection = vector_store_service.sanitize_collection_name(collection_name)
    
    try:
        collections = vector_store_service.get_all_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check collections: {e}")
        
    if sanitized_collection not in collections:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    try:
        collection = vector_store_service.client.get_collection(name=sanitized_collection)
        total_chunks = collection.count()
        
        file_name = f"{sanitized_collection}.pdf"
        peek = collection.get(limit=1)
        if peek and peek.get("metadatas") and len(peek["metadatas"]) > 0:
            file_name = peek["metadatas"][0].get("file_name", file_name)
            
        return StatsResponse(
            collection_name=sanitized_collection,
            total_chunks=total_chunks,
            file_name=file_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve collection stats: {e}")

@app.post("/query", response_model=QueryResponse)
def query_document(response: Response, payload: QueryRequest):
    """
    Executes a query against the vector store and passes context chunks to Groq LLM.
    """
    start_time = time.time()
    
    question = payload.question
    collection_name = payload.collection_name
    n_results = payload.n_results or 5
    
    is_all_docs = not collection_name or collection_name.lower() == "all"
    
    try:
        collections = vector_store_service.get_all_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collections: {e}")
        
    if not is_all_docs:
        sanitized_collection = vector_store_service.sanitize_collection_name(collection_name)
        if sanitized_collection not in collections:
            raise HTTPException(status_code=404, detail="Collection not found")
    else:
        sanitized_collection = None
        
    try:
        # 1. Embed query
        query_embeddings = embedding_service.get_embeddings([question])
        if not query_embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding.")
        query_embedding = query_embeddings[0]
        
        # 2. Query vector store
        if is_all_docs:
            similar_chunks = vector_store_service.search_all_collections(
                query_embedding=query_embedding,
                n_results_per_collection=3
            )
        else:
            similar_chunks = vector_store_service.search_similar(
                query_embedding=query_embedding,
                collection_name=sanitized_collection,
                n_results=n_results
            )
            
        # 3. Parse sources and calculate relevance score
        sources = []
        total_relevance = 0.0
        for chunk in similar_chunks:
            metadata = chunk.get("metadata", {})
            distance = chunk.get("distance", 0.0)
            
            # Convert L2 distance to score: 1 / (1 + distance)
            relevance_score = round(1.0 / (1.0 + distance), 4)
            total_relevance += relevance_score
            
            sources.append(
                SourceItem(
                    chunk_id=chunk.get("chunk_id", ""),
                    text=chunk.get("text", ""),
                    page_number=metadata.get("page_number", 0),
                    file_name=metadata.get("file_name", ""),
                    relevance_score=relevance_score
                )
            )
            
        # Compute confidence score
        confidence = round(total_relevance / len(similar_chunks), 4) if similar_chunks else 0.0
        warning = None
        if confidence < 0.3:
            warning = "Low confidence — the document may not contain relevant information"
            
        # 4. Generate response via LLM
        llm_response = llm_service.generate_answer(question, similar_chunks, is_multi_doc=is_all_docs)
        
        # Determine documents searched
        documents_searched = []
        if is_all_docs:
            for col_name in collections:
                file_name = f"{col_name}.pdf"
                try:
                    collection = vector_store_service.client.get_collection(name=col_name)
                    peek = collection.get(limit=1)
                    if peek and peek.get("metadatas") and len(peek["metadatas"]) > 0:
                        file_name = peek["metadatas"][0].get("file_name", file_name)
                except Exception:
                    pass
                documents_searched.append(file_name)
        else:
            file_name = f"{sanitized_collection}.pdf"
            try:
                collection = vector_store_service.client.get_collection(name=sanitized_collection)
                peek = collection.get(limit=1)
                if peek and peek.get("metadatas") and len(peek["metadatas"]) > 0:
                    file_name = peek["metadatas"][0].get("file_name", file_name)
            except Exception:
                pass
            documents_searched.append(file_name)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in query pipeline: {e}")
        
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}"
    
    return QueryResponse(
        question=question,
        answer=llm_response["answer"],
        sources=sources,
        pages_referenced=llm_response["pages_referenced"],
        model_used=llm_response["model_used"],
        confidence=confidence,
        warning=warning,
        documents_searched=documents_searched
    )

@app.post("/query/stream")
def query_document_stream(payload: QueryRequest):
    """
    Streams the answers for a query against the vector store in real-time.
    """
    question = payload.question
    collection_name = payload.collection_name
    n_results = payload.n_results or 5
    
    is_all_docs = not collection_name or collection_name.lower() == "all"
    
    try:
        collections = vector_store_service.get_all_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collections: {e}")
        
    if not is_all_docs:
        sanitized_collection = vector_store_service.sanitize_collection_name(collection_name)
        if sanitized_collection not in collections:
            raise HTTPException(status_code=404, detail="Collection not found")
    else:
        sanitized_collection = None
        
    try:
        # Generate query embedding
        query_embeddings = embedding_service.get_embeddings([question])
        if not query_embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding.")
        query_embedding = query_embeddings[0]
        
        # Search similarities
        if is_all_docs:
            similar_chunks = vector_store_service.search_all_collections(
                query_embedding=query_embedding,
                n_results_per_collection=3
            )
        else:
            similar_chunks = vector_store_service.search_similar(
                query_embedding=query_embedding,
                collection_name=sanitized_collection,
                n_results=n_results
            )
        
        def event_generator():
            try:
                # Stream the chunks of answer text from Groq
                for text_segment in llm_service.generate_answer_stream(question, similar_chunks, is_multi_doc=is_all_docs):
                    # Format as server-sent events
                    yield f"data: {text_segment}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: Error: {e}\n\n"
                yield "data: [DONE]\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming query setup failed: {e}")
