import os
import sys
import fitz  # PyMuPDF

# Ensure parent directory (backend) is in Python path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class PDFService:
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
        print("[PDFService] Initialized.")

    def extract_text_from_pdf(self, file_path: str) -> list[dict]:
        """
        Extracts text page-by-page from a PDF file.
        Returns a list of dicts: [{"page_number": int, "text": str, "file_name": str}]
        """
        pages_data = []
        file_name = os.path.basename(file_path)
        print(f"[PDFService] Extracting text from {file_name}...")
        
        try:
            doc = fitz.open(file_path)
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                text = page.get_text()
                pages_data.append({
                    "page_number": page_num,
                    "text": text,
                    "file_name": file_name
                })
            doc.close()
            print(f"[PDFService] Successfully extracted {len(pages_data)} pages from {file_name}.")
        except Exception as e:
            print(f"[PDFService] Error extracting text from {file_path}: {e}")
            raise e
            
        return pages_data

    def chunk_text(self, pages: list[dict]) -> list[dict]:
        """
        Splits text from pages into chunks of config.CHUNK_SIZE with config.CHUNK_OVERLAP overlap.
        Each chunk is returned as a dict:
        {"chunk_id": str, "text": str, "page_number": int, "file_name": str}
        """
        chunks = []
        print(f"[PDFService] Chunking {len(pages)} pages (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})...")
        
        try:
            for page in pages:
                text = page["text"]
                page_num = page["page_number"]
                file_name = page["file_name"]
                
                # Skip empty pages
                if not text or not text.strip():
                    continue
                
                text_len = len(text)
                start = 0
                chunk_idx = 0
                step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
                
                # Safety fallback to prevent infinite loops if overlap >= size
                if step <= 0:
                    step = config.CHUNK_SIZE if config.CHUNK_SIZE > 0 else 1
                
                while start < text_len:
                    end = min(start + config.CHUNK_SIZE, text_len)
                    chunk_text = text[start:end]
                    
                    # chunk_id format: "{file_name}_page{page_number}_chunk{chunk_index}"
                    chunk_id = f"{file_name}_page{page_num}_chunk{chunk_idx}"
                    
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "page_number": page_num,
                        "file_name": file_name
                    })
                    
                    # If we reached the end of the text, break
                    if end == text_len:
                        break
                        
                    start += step
                    chunk_idx += 1
                    
            print(f"[PDFService] Generated {len(chunks)} chunks.")
        except Exception as e:
            print(f"[PDFService] Error chunking text: {e}")
            raise e
            
        return chunks

pdf_service = PDFService()
