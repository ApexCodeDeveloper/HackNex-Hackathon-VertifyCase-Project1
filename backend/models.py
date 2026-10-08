from typing import Any, List, Optional
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
    db_backend: str = "sqlite"

# --- Conversation history ------------------------------------------------- #

class StoredMessage(BaseModel):
    message_id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[Any] = None
    created_at: str

class ConversationResponse(BaseModel):
    conversation_id: str
    messages: List[StoredMessage] = Field(default_factory=list)

class ConversationListItem(BaseModel):
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0

class ConversationCreateRequest(BaseModel):
    conversation_id: Optional[str] = None
    title: Optional[str] = None

class ConversationUpdateRequest(BaseModel):
    title: str

# --- Legal drafting ------------------------------------------------------- #

class DraftRequest(BaseModel):
    document_ids: List[str] = Field(default_factory=list)  # empty = all documents
    doc_type: str = "general"  # motion | memorandum | demand_letter | contract_clause | general
    instructions: str = ""     # free-form guidance for the draft

class DraftResponse(BaseModel):
    doc_type: str
    draft_text: str
    claims: List[GroundedClaim]
    sources: List[EvidenceChunk]
    confidence: str
    missing_information: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
