import os
from dotenv import load_dotenv

# Define directories relative to this file's position
# config.py is in project_root/backend/
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Load environment variables from the .env file in the project root
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path)

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Directory configurations
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# Ensure required directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Model settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"

# Chunking parameters
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

print(f"[Config] Project Root: {PROJECT_ROOT}")
print(f"[Config] Upload Dir: {UPLOAD_DIR}")
print(f"[Config] Chroma Dir: {CHROMA_DIR}")
if not GROQ_API_KEY:
    print("[Config] WARNING: GROQ_API_KEY is not loaded.")
else:
    print("[Config] GROQ_API_KEY loaded successfully.")
