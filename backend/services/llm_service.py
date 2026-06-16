import os
import sys
import re
from groq import Groq

# Ensure parent directory (backend) is in Python path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class LLMService:
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
        print("[LLMService] Initializing Groq client...")
        try:
            self.client = Groq(api_key=config.GROQ_API_KEY)
            print("[LLMService] Groq client initialized successfully.")
        except Exception as e:
            print(f"[LLMService] Error initializing Groq client: {e}")
            raise e

    def generate_answer(self, question: str, context_chunks: list[dict], is_multi_doc: bool = False) -> dict:
        """
        Generates an answer to the question using context_chunks with citations.
        Returns a dict: {"answer": str, "pages_referenced": list[int], "model_used": str}
        """
        print(f"[LLMService] Generating answer for question: '{question}' (is_multi_doc={is_multi_doc})...")
        
        try:
            # Build context string
            context_lines = []
            available_pages = set()
            for chunk in context_chunks:
                metadata = chunk.get("metadata", {})
                page_num = metadata.get("page_number", "Unknown")
                text = chunk.get("text", "")
                
                if is_multi_doc:
                    file_name = metadata.get("file_name", "Unknown Document")
                    context_lines.append(f"[Document: {file_name}, Page {page_num}]: {text}")
                else:
                    context_lines.append(f"[Page {page_num}]: {text}")
                
                if isinstance(page_num, int):
                    available_pages.add(page_num)
                elif isinstance(page_num, str) and page_num.isdigit():
                    available_pages.add(int(page_num))
            
            context_str = "\n".join(context_lines)
            
            # Format prompt as required
            if is_multi_doc:
                system_prompt = (
                    "You are a helpful assistant that answers questions based strictly "
                    "on the provided document context. You are answering based on MULTIPLE documents. "
                    "Always cite both the document name and page number for every claim you make."
                )
            else:
                system_prompt = (
                    "You are a helpful assistant that answers questions based strictly "
                    "on the provided document context. Always cite the page numbers you used."
                )
            
            user_prompt = (
                f"Context from document:\n{context_str}\n\n"
                f"Question: {question}\n\n"
                f"Answer the question based only on the context above. At the end, list which "
                f"pages you referenced."
            )
            
            # Call Groq API
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=config.GROQ_MODEL,
                temperature=0.0  # Keep temperature low for RAG accuracy
            )
            
            answer = response.choices[0].message.content
            
            # Parse referenced pages from response
            referenced_pages = set()
            for num_str in re.findall(r'\b\d+\b', answer):
                num = int(num_str)
                if num in available_pages:
                    referenced_pages.add(num)
                    
            return {
                "answer": answer,
                "pages_referenced": sorted(list(referenced_pages)),
                "model_used": config.GROQ_MODEL
            }
            
        except Exception as e:
            # Check if it's a 429 Rate Limit error
            if (hasattr(e, 'status_code') and e.status_code == 429) or \
               ("rate limit" in str(e).lower()) or \
               ("429" in str(e)):
                print(f"[LLMService] Groq Rate Limit (429) detected: {e}")
                return {
                    "answer": "Rate limit reached. Please wait a moment and try again.",
                    "pages_referenced": [],
                    "model_used": config.GROQ_MODEL
                }
    def generate_answer_stream(self, question: str, context_chunks: list[dict], is_multi_doc: bool = False):
        """
        Generates a streaming answer to the question using context_chunks.
        Yields text segments.
        """
        print(f"[LLMService] Streaming answer for question: '{question}' (is_multi_doc={is_multi_doc})...")
        try:
            context_lines = []
            for chunk in context_chunks:
                metadata = chunk.get("metadata", {})
                page_num = metadata.get("page_number", "Unknown")
                text = chunk.get("text", "")
                
                if is_multi_doc:
                    file_name = metadata.get("file_name", "Unknown Document")
                    context_lines.append(f"[Document: {file_name}, Page {page_num}]: {text}")
                else:
                    context_lines.append(f"[Page {page_num}]: {text}")
            
            context_str = "\n".join(context_lines)
            
            if is_multi_doc:
                system_prompt = (
                    "You are a helpful assistant that answers questions based strictly "
                    "on the provided document context. You are answering based on MULTIPLE documents. "
                    "Always cite both the document name and page number for every claim you make."
                )
            else:
                system_prompt = (
                    "You are a helpful assistant that answers questions based strictly "
                    "on the provided document context. Always cite the page numbers you used."
                )
            
            user_prompt = (
                f"Context from document:\n{context_str}\n\n"
                f"Question: {question}\n\n"
                f"Answer the question based only on the context above. At the end, list which "
                f"pages you referenced."
            )
            
            # Call Groq API in streaming mode
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=config.GROQ_MODEL,
                temperature=0.0,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                        
        except Exception as e:
            if (hasattr(e, 'status_code') and e.status_code == 429) or \
               ("rate limit" in str(e).lower()) or \
               ("429" in str(e)):
                print(f"[LLMService] Groq Rate Limit (429) detected during streaming: {e}")
                yield "Rate limit reached. Please wait a moment and try again."
            else:
                print(f"[LLMService] Error in streaming answer: {e}")
                yield f"Error: {e}"

llm_service = LLMService()
