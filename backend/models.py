from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    document_id: str
    document_name: str
    file_size: int
    page_count: int
    chunk_count: int
    created_at: str

class EvidenceChunk(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    text: str
    relevance_score: Optional[float] = None
    section: Optional[str] = None

class GroundedClaim(BaseModel):
    claim: str
    source_ids: List[str]

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    document_ids: Optional[List[str]] = None

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    claims: List[GroundedClaim]
    sources: List[EvidenceChunk]
    confidence: str
    missing_information: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)

class ContradictionItem(BaseModel):
    topic: str
    claim_a: dict
    claim_b: dict
    explanation: str

class ContradictionsResponse(BaseModel):
    contradictions: List[ContradictionItem]
    message: Optional[str] = None

class CaseReviewRequest(BaseModel):
    document_ids: List[str]

class CaseReviewResponse(BaseModel):
    document_ids: List[str]
    document_names: List[str]
    key_facts: List[GroundedClaim]
    sources: List[EvidenceChunk]
    contradictions: List[ContradictionItem]
    missing_information: List[str]
    confidence: str
    summary: str

class HealthResponse(BaseModel):
    status: str
    backend: str
    chroma_ready: bool
    gemini_configured: bool
    indexed_documents: int
