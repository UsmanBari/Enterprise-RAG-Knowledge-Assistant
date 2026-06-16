import os
import sys
import re
# pyrefly: ignore [missing-import]
import chromadb

# Ensure parent directory (backend) is in Python path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class VectorStoreService:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        print(f"[VectorStoreService] Initializing ChromaDB at '{config.CHROMA_DIR}'...")
        try:
            self.client = chromadb.PersistentClient(path=config.CHROMA_DIR)
            print("[VectorStoreService] ChromaDB client initialized successfully.")
        except Exception as e:
            print(f"[VectorStoreService] Error initializing ChromaDB client: {e}")
            raise e

    def sanitize_collection_name(self, name: str) -> str:
        """
        Sanitizes a name to make it a valid ChromaDB collection name:
        - 3-63 characters
        - starts and ends with alphanumeric
        - contains only alphanumeric, underscores, or hyphens
        - lowercase preferred (case-insensitive checks)
        """
        # Lowercase and remove extension if any
        name_lower = name.lower()
        if name_lower.endswith('.pdf'):
            name_lower = name_lower[:-4]
            
        # Replace non-alphanumeric/hyphen/underscore with underscore
        sanitized = re.sub(r'[^a-z0-9_-]', '_', name_lower)
        
        # Replace consecutive underscores/hyphens
        sanitized = re.sub(r'__+', '_', sanitized)
        sanitized = re.sub(r'--+', '-', sanitized)
        
        # Trim length to 63 chars max
        sanitized = sanitized[:63]
        
        # Strip leading/trailing underscores/hyphens
        sanitized = sanitized.strip('_-')
        
        # Ensure minimum length of 3
        if len(sanitized) < 3:
            sanitized = f"{sanitized}col"[:3]
            
        # Ensure it starts and ends with alphanumeric
        if not sanitized[0].isalnum():
            sanitized = 'a' + sanitized[1:]
        if not sanitized[-1].isalnum():
            sanitized = sanitized[:-1] + 'z'
            
        return sanitized

    def add_document(self, chunks: list[dict], embeddings: list[list[float]], collection_name: str):
        """
        Stores chunks with their embeddings and metadata (page_number, file_name, chunk_id).
        """
        sanitized_name = self.sanitize_collection_name(collection_name)
        print(f"[VectorStoreService] Adding {len(chunks)} chunks to collection '{sanitized_name}'...")
        
        try:
            collection = self.client.get_or_create_collection(name=sanitized_name)
            
            ids = [chunk["chunk_id"] for chunk in chunks]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [
                {
                    "page_number": chunk["page_number"],
                    "file_name": chunk["file_name"],
                    "chunk_id": chunk["chunk_id"]
                }
                for chunk in chunks
            ]
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            print(f"[VectorStoreService] Successfully added document chunks to collection '{sanitized_name}'.")
        except Exception as e:
            print(f"[VectorStoreService] Error adding document chunks to collection '{sanitized_name}': {e}")
            raise e

    def search_similar(self, query_embedding: list[float], collection_name: str, n_results: int = 5) -> list[dict]:
        """
        Returns top n_results similar chunks with their metadata and distance scores.
        """
        sanitized_name = self.sanitize_collection_name(collection_name)
        print(f"[VectorStoreService] Searching similar chunks in collection '{sanitized_name}' (n_results={n_results})...")
        
        try:
            collection = self.client.get_collection(name=sanitized_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            formatted_results = []
            if results and "ids" in results and results["ids"]:
                ids = results["ids"][0]
                distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
                metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(ids)
                documents = results["documents"][0] if "documents" in results and results["documents"] else [""] * len(ids)
                
                for i in range(len(ids)):
                    formatted_results.append({
                        "chunk_id": ids[i],
                        "distance": distances[i],
                        "metadata": metadatas[i],
                        "text": documents[i]
                    })
            print(f"[VectorStoreService] Found {len(formatted_results)} results.")
            return formatted_results
        except Exception as e:
            print(f"[VectorStoreService] Error searching similar chunks in collection '{sanitized_name}': {e}")
            raise e

    def get_all_collections(self) -> list[str]:
        """
        Returns list of all collection names.
        """
        print("[VectorStoreService] Fetching all collections...")
        try:
            collections = self.client.list_collections()
            names = [col.name for col in collections]
            print(f"[VectorStoreService] Current collections: {names}")
            return names
        except Exception as e:
            print(f"[VectorStoreService] Error fetching collections: {e}")
            raise e

    def search_all_collections(self, query_embedding: list[float], n_results_per_collection: int = 3) -> list[dict]:
        """
        Searches all collection indexes and returns the top 8 overall results, sorted by relevance score.
        """
        print("[VectorStoreService] Searching all collections...")
        all_results = []
        try:
            collections = self.get_all_collections()
            for col_name in collections:
                try:
                    # Search similar items in this collection
                    results = self.search_similar(query_embedding, col_name, n_results=n_results_per_collection)
                    for item in results:
                        # Ensure metadata has file_name and collection_name
                        metadata = item.get("metadata") or {}
                        if "file_name" not in metadata:
                            metadata["file_name"] = f"{col_name}.pdf"
                        metadata["collection_name"] = col_name
                        item["metadata"] = metadata
                        all_results.append(item)
                except Exception as ex:
                    print(f"[VectorStoreService] Warning: Search failed for collection {col_name}: {ex}")
            
            # Sort all merged results by distance ascending
            all_results.sort(key=lambda x: x.get("distance", 999.0))
            
            # Return top 8
            top_results = all_results[:8]
            print(f"[VectorStoreService] search_all_collections returned {len(top_results)} results out of {len(all_results)} total chunks retrieved.")
            return top_results
        except Exception as e:
            print(f"[VectorStoreService] Error in search_all_collections: {e}")
            raise e

    def delete_collection(self, collection_name: str):
        """
        Deletes a collection by name.
        """
        sanitized_name = self.sanitize_collection_name(collection_name)
        print(f"[VectorStoreService] Deleting collection '{sanitized_name}'...")
        try:
            self.client.delete_collection(name=sanitized_name)
            print(f"[VectorStoreService] Collection '{sanitized_name}' deleted successfully.")
        except Exception as e:
            print(f"[VectorStoreService] Error deleting collection '{sanitized_name}': {e}")
            raise e

vector_store_service = VectorStoreService()
