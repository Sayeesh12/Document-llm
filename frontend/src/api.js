const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"
const API_KEY = import.meta.env.VITE_API_KEY || "dev-api-key-12345"

export const apiHeaders = { "X-API-Key": API_KEY }

export async function processDocument(file, documentType) {
  const formData = new FormData()
  formData.append("file", file)
  if (documentType && documentType !== "auto") {
    formData.append("document_type", documentType)
  }

  const response = await fetch(`${API_BASE}/documents/process`, {
    method: "POST",
    headers: apiHeaders,
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || "Processing failed")
  }

  return response.json()
}

export async function getDocuments(limit = 10) {
  const response = await fetch(`${API_BASE}/documents?limit=${limit}`, {
    headers: apiHeaders
  })

  if (!response.ok) {
    throw new Error("Failed to fetch documents")
  }

  return response.json()
}

export async function getDocument(documentId) {
  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    headers: apiHeaders
  })

  if (!response.ok) {
    throw new Error("Failed to fetch document")
  }

  return response.json()
}

export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: "DELETE",
    headers: apiHeaders
  })

  if (!response.ok) {
    throw new Error("Failed to delete document")
  }

  return response.json()
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`)
    return response.ok
  } catch {
    return false
  }
}

export { API_BASE }
