from pydantic import BaseModel, Field
from typing import List, Optional

# --- /health Response Schema ---
class HealthResponse(BaseModel):
    status: str
    chromadb: str
    embedding_model: str
    groq: str

# --- /upload Response Schema ---
class UploadResponse(BaseModel):
    success: bool
    file_name: str
    collection_name: str
    total_pages: int
    total_chunks: int
    message: str

# --- /documents Response Schema ---
class DocumentItem(BaseModel):
    collection_name: str
    file_name: str
    file_exists: bool

class DocumentsResponse(BaseModel):
    documents: List[DocumentItem]
    total: int

# --- /documents/{collection_name}/stats Response Schema ---
class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    file_name: str

# --- /query Request Schema ---
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="The query question for the document.")
    collection_name: Optional[str] = Field(default=None, description="The query collection name. If null or 'all', queries all documents.")
    n_results: Optional[int] = Field(default=5, ge=1, le=10, description="Number of results to retrieve (1-10).")

# --- /query Response Schema ---
class SourceItem(BaseModel):
    chunk_id: str
    text: str
    page_number: int
    file_name: str
    relevance_score: float

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceItem]
    pages_referenced: List[int]
    model_used: str
    confidence: Optional[float] = Field(default=None, description="Average relevance score of sources.")
    warning: Optional[str] = Field(default=None, description="Warning if low semantic confidence.")
    documents_searched: Optional[List[str]] = Field(default=None, description="List of document filenames searched.")

# --- Generic Success Response ---
class DeleteResponse(BaseModel):
    success: bool
    message: str
