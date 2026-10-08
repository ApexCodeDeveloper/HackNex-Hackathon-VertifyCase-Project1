import os
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pypdf
from config import STORAGE_PATH, CHUNK_SIZE, CHUNK_OVERLAP
import database

def extract_text_by_pages(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF page by page, tracking exact 1-indexed page numbers."""
    pages = []
    reader = pypdf.PdfReader(pdf_path)
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        # Clean up excess whitespace while preserving structure
        text = re.sub(r'[ \t]+', ' ', text).strip()
        pages.append({
            "page_number": page_num,
            "text": text
        })
    return pages

def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into manageable chunks respecting sentence or paragraph boundaries."""
    if not text:
        return []
    
    # Try splitting by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]
        
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If paragraph itself is larger than chunk_size, split by sentences or hard length
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.?!])\s+', para)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) + 1 <= chunk_size:
                        sub_chunk = (sub_chunk + " " + s).strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        # If a single sentence is super long, slice it
                        while len(s) > chunk_size:
                            chunks.append(s[:chunk_size])
                            s = s[chunk_size - chunk_overlap:]
                        sub_chunk = s
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = para
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def process_pdf_document(file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Saves document, extracts pages, chunks text with exact page provenance.
    Returns (document_metadata, list_of_chunks).
    """
    document_id = str(uuid.uuid4())
    safe_filename = Path(filename).name
    target_path = Path(STORAGE_PATH) / f"{document_id}_{safe_filename}"
    
    with open(target_path, "wb") as f:
        f.write(file_bytes)
        
    file_size = len(file_bytes)
    
    # Extract text page by page
    pages_data = extract_text_by_pages(str(target_path))
    page_count = len(pages_data)
    
    all_chunks = []
    for page in pages_data:
        page_num = page["page_number"]
        page_text = page["text"]
        if not page_text:
            continue
            
        chunks = split_text_into_chunks(page_text, CHUNK_SIZE, CHUNK_OVERLAP)
        for idx, chunk_str in enumerate(chunks):
            chunk_id = f"{document_id}_p{page_num}_c{idx+1}"
            all_chunks.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "document_name": safe_filename,
                "page_number": page_num,
                "text": chunk_str
            })
            
    created_at = datetime.now(timezone.utc).isoformat()
    
    doc_metadata = {
        "document_id": document_id,
        "document_name": safe_filename,
        "file_path": str(target_path),
        "file_size": file_size,
        "page_count": page_count,
        "chunk_count": len(all_chunks),
        "created_at": created_at
    }
    
    database.save_document(doc_metadata)
    
    return doc_metadata, all_chunks
