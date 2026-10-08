import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from config import CHROMA_PATH, GEMINI_API_KEY, TOP_K

_chroma_client = None
_collection = None

def get_chroma_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
        
    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # We will compute or use Chroma's standard embedding function
    # To ensure complete reliability even without external API dependency for embeddings,
    # we can use chromadb default or google genai if configured.
    # Chromadb's default embedding function requires onnxruntime which may be slow to init.
    # Let's provide a robust, resilient embedding mechanism.
    
    _collection = _chroma_client.get_or_create_collection(
        name="legal_documents",
        metadata={"hnsw:space": "cosine"}
    )
    return _collection

def index_chunks(chunks: List[Dict[str, Any]]):
    """Index chunks in ChromaDB with metadata."""
    if not chunks:
        return
        
    collection = get_chroma_collection()
    
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "page_number": int(c["page_number"])
        }
        for c in chunks
    ]
    
    # Chroma add handles batched additions
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )

def delete_document_chunks(document_id: str):
    """Remove chunks corresponding to a deleted document."""
    collection = get_chroma_collection()
    try:
        collection.delete(where={"document_id": document_id})
    except Exception as e:
        print(f"Error removing chunks for {document_id}: {e}")

def retrieve_evidence(query: str, document_ids: Optional[List[str]] = None, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Search ChromaDB for relevant chunks.
    Filters by document_ids if provided.
    Calculates normalized relevance scores.
    """
    collection = get_chroma_collection()
    
    where_clause = None
    if document_ids and len(document_ids) == 1:
        where_clause = {"document_id": document_ids[0]}
    elif document_ids and len(document_ids) > 1:
        where_clause = {"document_id": {"$in": document_ids}}
        
    total_chunks = collection.count()
    if total_chunks == 0:
        return []
        
    k = min(top_k, total_chunks)
    
    query_params = {
        "query_texts": [query],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where_clause:
        query_params["where"] = where_clause
        
    results = collection.query(**query_params)
    
    evidence_list = []
    if not results or not results.get("ids") or len(results["ids"][0]) == 0:
        return []
        
    for idx in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][idx]
        text = results["documents"][0][idx]
        metadata = results["metadatas"][0][idx]
        distance = results["distances"][0][idx] if "distances" in results and results["distances"] else 0.5
        
        # Convert cosine distance to cosine similarity score: 1.0 - distance
        relevance_score = max(0.0, min(1.0, 1.0 - float(distance)))
        
        evidence_list.append({
            "chunk_id": chunk_id,
            "document_id": metadata.get("document_id", ""),
            "document_name": metadata.get("document_name", ""),
            "page_number": int(metadata.get("page_number", 1)),
            "text": text,
            "relevance_score": round(relevance_score, 4)
        })
        
    return evidence_list

def get_chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    collection = get_chroma_collection()
    res = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
    if res and res.get("ids") and len(res["ids"]) > 0:
        return {
            "chunk_id": res["ids"][0],
            "document_id": res["metadatas"][0].get("document_id", ""),
            "document_name": res["metadatas"][0].get("document_name", ""),
            "page_number": int(res["metadatas"][0].get("page_number", 1)),
            "text": res["documents"][0]
        }
    return None

def get_chunks_for_documents(document_ids: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve sample of chunks across specified documents for broad comparative analysis."""
    collection = get_chroma_collection()
    if not document_ids:
        return []
        
    where_clause = {"document_id": document_ids[0]} if len(document_ids) == 1 else {"document_id": {"$in": document_ids}}
    res = collection.get(where=where_clause, limit=limit, include=["documents", "metadatas"])
    
    items = []
    if res and res.get("ids"):
        for i in range(len(res["ids"])):
            items.append({
                "chunk_id": res["ids"][i],
                "document_id": res["metadatas"][i].get("document_id", ""),
                "document_name": res["metadatas"][i].get("document_name", ""),
                "page_number": int(res["metadatas"][i].get("page_number", 1)),
                "text": res["documents"][i]
            })
    return items
