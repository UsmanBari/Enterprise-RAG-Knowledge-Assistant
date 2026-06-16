const API_BASE = "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let errorMsg = "An error occurred";
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorData.message || errorMsg;
    } catch (e) {
      // Fallback
    }
    throw new Error(errorMsg);
  }
  
  const data = await response.json();
  const processTime = response.headers.get("X-Process-Time");
  if (processTime && typeof data === "object") {
    data._processTime = processTime;
  }
  return data;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  
  return handleResponse(response);
}

export async function getDocuments() {
  const response = await fetch(`${API_BASE}/documents`);
  return handleResponse(response);
}

export async function deleteDocument(collectionName) {
  const response = await fetch(`${API_BASE}/documents/${collectionName}`, {
    method: "DELETE",
  });
  return handleResponse(response);
}

export async function getDocumentStats(collectionName) {
  const response = await fetch(`${API_BASE}/documents/${collectionName}/stats`);
  return handleResponse(response);
}

export async function queryDocument(question, collectionName, nResults = 5) {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      collection_name: collectionName === "all" ? null : collectionName,
      n_results: nResults,
    }),
  });
  
  return handleResponse(response);
}
