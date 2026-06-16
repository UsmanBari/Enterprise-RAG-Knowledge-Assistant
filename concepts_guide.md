# Developer Concept Guide: From Zero to RAG

This guide explains every core technology, tool, and design pattern used in the **Enterprise RAG Knowledge Assistant**, starting from the absolute basics.

---

## 1. What is RAG (Retrieval-Augmented Generation)?

Traditional Large Language Models (LLMs) are like smart students taking a closed-book exam. They can answer general questions using what they learned during training, but they cannot answer questions about your private files or brand-new data.

**RAG** solves this by turning the exam into an **open-book test**:
1. **Retrieve**: When you ask a question, the system searches your uploaded PDFs to find the most relevant paragraphs.
2. **Augment**: The system appends these paragraphs as "context" to your original question.
3. **Generate**: The system hands the question and the context to the LLM. The LLM reads the context and writes an accurate, factual answer citing the source.

---

## 2. Text Ingestion & Chunking (PyMuPDF)

When a PDF is uploaded, we cannot simply send the entire book to the LLM because:
- It exceeds the LLM's input limit (context window).
- It is expensive and slow.
- The LLM might miss details buried in hundreds of pages (called "lost in the middle").

### What we do:
* **Extraction (PyMuPDF / Fitz)**: We use PyMuPDF to extract plain text from the PDF, page by page.
* **Chunking**: We slice the text into smaller pieces (e.g., 500 characters each).
* **Chunk Overlap (50 characters)**: To make sure we don't accidentally split a sentence in half and lose its meaning, we overlap the chunks slightly:

```text
Chunk 1: "...Automated Operations Engineers write scripts to monitor systems."
                                                [Overlapping Area]
Chunk 2:                       "write scripts to monitor systems daily to prevent crashes."
```

---

## 3. Embeddings (all-MiniLM-L6-v2)

Computers do not understand English words, but they are great at math. To search for paragraphs based on *meaning* rather than exact keyword spelling, we use **Embeddings**.

### The Concept:
An **Embedding Model** is a neural network that translates text into a list of numbers (a vector). Our model, `all-MiniLM-L6-v2`, generates a list of **384 numbers** for every text chunk.
- These numbers represent coordinates in a 384-dimensional "concept space".
- Sentences with similar meanings are placed close to each other.
- For example, `"The server is down"` and `"Network services crashed"` will have very similar vector numbers, even though they share no common words.

---

## 4. Vector Databases (ChromaDB)

Traditional databases (like SQL or MongoDB) search data by matching exact strings or IDs. A **Vector Database** is designed specifically to store high-dimensional coordinate numbers (vectors) and search them by spatial distance.

### The search math:
* **Distance Metric**: We use **L2 Distance** (Euclidean distance) to measure how close two vectors are.
* **Similarity Score**: The backend converts this distance into a relevance percentage:
  $$\text{Relevance Score} = \frac{1}{1 + \text{Distance}}$$
  - A distance of `0` (exact match) converts to a `100%` relevance score.
  - Greater distances result in lower percentages.
* **Multi-Document Queries**: In multi-document mode, our server retrieves the top 3 matches from *each* uploaded PDF database, aggregates them, and selects the top 8 overall matches.

---

## 5. The API Layer (FastAPI & Uvicorn)

* **FastAPI**: A high-performance Python framework for building REST APIs. It handles input validation (e.g., checking if the query is between 3 and 500 characters) and formats Pydantic response models.
* **Uvicorn**: The actual server process that runs FastAPI and listens for incoming browser network requests.
* **CORS (Cross-Origin Resource Sharing)**: Security built into web browsers. Since the frontend runs on `localhost:5173` and the backend runs on `localhost:8000`, the browser would normally block communication. We configure CORS middleware in `main.py` to allow cross-origin requests.

---

## 6. The LLM (Groq & LLaMA 3.1)

* **LLaMA 3.1 8B**: An open-weights state-of-the-art model developed by Meta. It is smart, fast, and optimized for reasoning over contexts.
* **Groq Cloud**: An API hosting provider that uses specialized hardware (LPUs) to execute LLM queries at speeds exceeding 400 tokens per second.
* **Prompt Engineering**: The backend injects the matching text chunks into a template.
  * **System Prompt**: *"You are a helpful assistant that answers questions based strictly on the context..."*
  * **User Prompt**: *"Here is the context: [Page 1]: text... Question: ... "*
  * **Citations parsing**: We run a regular expression over the LLM output to extract integers matching the retrieved page numbers, rendering them as tags in the UI.

---

## 7. Frontend Architecture (React, Vite & CSS)

* **Vite**: A modern frontend builder that compiles React components instantly.
* **Components**:
  * `Sidebar.jsx` (List of files + "All Documents" toggle + shimmer skeletons).
  * `ChatView.jsx` (Messages container + text input + export helper).
  * `MessageBubble.jsx` (User and AI dialogue cards + progress bar confidence ratings + source accordion headers).
* **Keyboard Listener**: Registers event listeners on the browser `window` object:
  * `Ctrl+U` intercepts the default print dialog and clicks the hidden file upload input.
  * `Escape` resets selection states.
* **CSS Animations**: Uses keyframes for layout effects:
  * `@keyframes skeletonPulse`: Shimmers grey list items by shifting gradient backgrounds.
  * `@keyframes toastSlideIn`: Moves toast bubbles onto the screen from off-right.

---

## 8. Cloud Containerization (Docker)

* **Containers**: Think of Docker as a shipping container. Instead of worrying if your server has Python installed or correct libraries, a **Dockerfile** packages Python, your code, dependencies, and configuration into a single package.
* **Hugging Face Spaces**: Runs your Docker container on their free CPU servers, exposing port `7860` as a public API web link for your frontend to query.
