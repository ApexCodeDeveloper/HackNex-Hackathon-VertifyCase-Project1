import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, CORS_ORIGIN_REGEX, STORAGE_PATH, GEMINI_API_KEY
import database
import documents
import rag
import reasoning
import verification
from models import (
    DocumentMetadata,
    ChatRequest,
    ChatResponse,
    EvidenceChunk,
    ContradictionsResponse,
    ContradictionItem,
    CaseReviewRequest,
    CaseReviewResponse,
    HealthResponse,
    ConversationResponse,
    ConversationListItem,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    DraftRequest,
    DraftResponse,
)

database.init_db()

app = FastAPI(
    title="VertifyCase — Agentic Legal Assistant",
    description="Grounded Legal Document Intelligence Workstation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STORAGE_PATH):
    app.mount("/files", StaticFiles(directory=STORAGE_PATH), name="files")

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    stats = database.count_all_stats()
    chroma_ok = False
    chroma_chunks = 0
    try:
        col = rag.get_chroma_collection()
        chroma_chunks = int(col.count())
        chroma_ok = True
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        backend="FastAPI",
        chroma_ready=chroma_ok,
        gemini_configured=bool(GEMINI_API_KEY and len(GEMINI_API_KEY.strip()) > 5),
        indexed_documents=stats["documents"],
        db_backend=database.BACKEND.name,
        chroma_chunks=chroma_chunks,
    )

@app.get("/api/stats")
def get_stats():
    return database.count_all_stats()

@app.post("/api/documents/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported.")
    
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")

    try:
        doc_meta, chunks = documents.process_pdf_document(content, file.filename)
        try:
            rag.index_chunks(chunks)
        except Exception as index_err:
            # Roll back so a half-indexed document never appears in listings
            database.delete_document(doc_meta["document_id"])
            rag.delete_document_chunks(doc_meta["document_id"])
            if os.path.exists(doc_meta["file_path"]):
                try:
                    os.remove(doc_meta["file_path"])
                except Exception:
                    pass
            raise index_err
        return DocumentMetadata(**doc_meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.get("/api/documents", response_model=List[DocumentMetadata])
def list_documents():
    docs = database.get_all_documents()
    return [DocumentMetadata(**d) for d in docs]

@app.get("/api/documents/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    doc = database.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentMetadata(**doc)

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    doc = database.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    rag.delete_document_chunks(document_id)
    database.delete_document(document_id)
    if os.path.exists(doc["file_path"]):
        try:
            os.remove(doc["file_path"])
        except Exception:
            pass
            
    return {"status": "success", "message": f"Document {doc['document_name']} deleted."}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_msg_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    # Ensure the conversation row exists and derive a title from the first message
    try:
        existing = database.get_conversation(conversation_id)
        if existing is None:
            auto_title = request.message.strip()[:60] or "New conversation"
            database.save_conversation(
                conversation_id=conversation_id,
                created_at=now_str,
                title=auto_title,
                updated_at=now_str,
            )
        else:
            database.update_conversation(conversation_id, updated_at=now_str)
    except Exception:
        pass

    database.save_message(
        conversation_id=conversation_id,
        message_id=user_msg_id,
        role="user",
        content=request.message,
        created_at=now_str
    )

    evidence = rag.retrieve_evidence(
        query=request.message,
        document_ids=request.document_ids
    )

    history = database.get_conversation_messages(conversation_id)

    raw_ai = reasoning.generate_grounded_answer(
        query=request.message,
        evidence_chunks=evidence,
        conversation_history=history[:-1]
    )

    answer, claims, sources, confidence, missing, contradictions = verification.verify_and_clamp_response(
        ai_response=raw_ai,
        retrieved_evidence=evidence
    )

    asst_msg_id = str(uuid.uuid4())
    resp_metadata = {
        "claims": [c.model_dump() for c in claims],
        "sources": [s.model_dump() for s in sources],
        "confidence": confidence,
        "missing_information": missing,
        "contradictions": contradictions
    }
    database.save_message(
        conversation_id=conversation_id,
        message_id=asst_msg_id,
        role="assistant",
        content=answer,
        metadata=resp_metadata,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    # Bump updated_at so the conversation sorts to the top of history
    try:
        database.update_conversation(
            conversation_id, updated_at=datetime.now(timezone.utc).isoformat()
        )
    except Exception:
        pass

    return ChatResponse(
        conversation_id=conversation_id,
        answer=answer,
        claims=claims,
        sources=sources,
        confidence=confidence,
        missing_information=missing,
        contradictions=contradictions
    )

@app.get("/api/conversations", response_model=List[ConversationListItem])
def list_conversations(limit: int = Query(100, ge=1, le=500)):
    """Return the conversation list for the chat-history panel, newest first."""
    try:
        rows = database.list_conversations(limit)
        return [ConversationListItem(**r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversations", response_model=ConversationListItem)
def create_conversation(req: Optional[ConversationCreateRequest] = None):
    """Create a new (empty) conversation for the chat-history panel."""
    conversation_id = (req.conversation_id if req and req.conversation_id else None) or str(uuid.uuid4())
    title = (req.title if req and req.title else None) or "New conversation"
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        database.save_conversation(
            conversation_id=conversation_id,
            created_at=now_str,
            title=title,
            updated_at=now_str,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ConversationListItem(
        conversation_id=conversation_id,
        title=title,
        created_at=now_str,
        updated_at=now_str,
        message_count=0,
    )


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str):
    """Return all messages for a conversation."""
    try:
        msgs = database.get_conversation_messages(conversation_id)
        return {"conversation_id": conversation_id, "messages": msgs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/conversations/{conversation_id}", response_model=ConversationListItem)
def rename_conversation(conversation_id: str, req: ConversationUpdateRequest):
    """Rename a conversation in the chat-history panel."""
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        existing = database.get_conversation(conversation_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        database.update_conversation(conversation_id, title=req.title, updated_at=now_str)
        updated = database.get_conversation(conversation_id) or {}
        return ConversationListItem(
            conversation_id=conversation_id,
            title=req.title,
            created_at=updated.get("created_at", now_str),
            updated_at=now_str,
            message_count=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete a conversation and all of its messages from the chat history."""
    try:
        database.delete_conversation(conversation_id)
        return {"status": "success", "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/draft", response_model=DraftResponse)
def draft_document(req: DraftRequest):
    """Draft a grounded legal document (motion, memo, letter, clause, general)
    using only facts verified against the selected documents' evidence."""
    if req.instructions.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Provide drafting instructions describing what to draft.",
        )

    doc_ids = req.document_ids
    if not doc_ids:
        doc_ids = [d["document_id"] for d in database.get_all_documents()]
    if not doc_ids:
        raise HTTPException(
            status_code=400,
            detail="No documents available to draft from — upload PDFs first.",
        )

    # Retrieve evidence for the requested documents.
    chunks = rag.get_chunks_for_documents(doc_ids, limit=30)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No evidence chunks could be retrieved from the selected documents.",
        )

    # Generate + verify through the same grounding pipeline as chat/case-review.
    raw = reasoning.draft_legal_document(req.instructions, chunks, doc_type=req.doc_type)
    draft_text, claims, sources, confidence, missing, contradictions = (
        verification.verify_and_clamp_response(ai_response=raw, retrieved_evidence=chunks)
    )

    return DraftResponse(
        doc_type=req.doc_type,
        draft_text=draft_text,
        claims=claims,
        sources=sources,
        confidence=confidence,
        missing_information=missing,
        contradictions=contradictions,
    )


@app.get("/api/evidence/{chunk_id}")
def get_evidence_chunk(chunk_id: str):
    chunk = rag.get_chunk_by_id(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Evidence chunk not found.")
    return chunk

@app.post("/api/analyze/contradictions", response_model=ContradictionsResponse)
def analyze_contradictions(req: Optional[CaseReviewRequest] = None):
    doc_ids = req.document_ids if req and req.document_ids else []
    if not doc_ids:
        docs = database.get_all_documents()
        doc_ids = [d["document_id"] for d in docs]

    if len(doc_ids) < 2:
        return ContradictionsResponse(
            contradictions=[],
            message="Contradiction detection requires at least 2 indexed documents."
        )

    chunks = rag.get_chunks_for_documents(doc_ids, limit=25)
    if not chunks:
        return ContradictionsResponse(
            contradictions=[],
            message="No evidence chunks could be retrieved from the selected documents."
        )
    if not reasoning.get_gemini_client():
        return ContradictionsResponse(
            contradictions=[],
            message="AI analysis is temporarily unavailable. GEMINI_API_KEY is not configured."
        )

    contradictions_raw = reasoning.analyze_document_contradictions(chunks)
    
    items = []
    for c in contradictions_raw:
        items.append(ContradictionItem(
            topic=c.get("topic", "Factual Discrepancy"),
            claim_a=c.get("claim_a", {}),
            claim_b=c.get("claim_b", {}),
            explanation=c.get("explanation", "")
        ))

    msg = "No supported contradictions found in the selected documents." if not items else None
    return ContradictionsResponse(contradictions=items, message=msg)

@app.post("/api/analyze/case-review", response_model=CaseReviewResponse)
def review_case(req: CaseReviewRequest):
    if not req.document_ids:
        raise HTTPException(status_code=400, detail="No document IDs specified.")

    docs = [database.get_document_by_id(did) for did in req.document_ids if database.get_document_by_id(did)]
    doc_names = [d["document_name"] for d in docs]
    chunks = rag.get_chunks_for_documents(req.document_ids, limit=30)

    review_data = reasoning.review_case_documents(chunks)

    valid_chunks_map = {c["chunk_id"]: c for c in chunks}
    verified_facts = []
    for f in review_data.get("key_facts", []):
        text = f.get("claim", "")
        valid_sids = [sid for sid in f.get("source_ids", []) if sid in valid_chunks_map]
        if text and valid_sids:
            verified_facts.append(verification.GroundedClaim(claim=text, source_ids=valid_sids))

    sources = [EvidenceChunk(**c) for c in chunks[:5]]
    
    contradictions = []
    for c in review_data.get("contradictions", []):
        contradictions.append(ContradictionItem(
            topic=c.get("topic", "Contradiction"),
            claim_a=c.get("claim_a", {}),
            claim_b=c.get("claim_b", {}),
            explanation=c.get("explanation", "")
        ))

    return CaseReviewResponse(
        document_ids=req.document_ids,
        document_names=doc_names,
        key_facts=verified_facts,
        sources=sources,
        contradictions=contradictions,
        missing_information=review_data.get("missing_information", []),
        confidence=review_data.get("confidence", "medium"),
        summary=review_data.get("summary", "")
    )

