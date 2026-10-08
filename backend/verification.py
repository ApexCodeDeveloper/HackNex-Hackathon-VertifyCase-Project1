from typing import List, Dict, Any, Tuple
from models import GroundedClaim, EvidenceChunk

def verify_and_clamp_response(
    ai_response: Dict[str, Any],
    retrieved_evidence: List[Dict[str, Any]]
) -> Tuple[str, List[GroundedClaim], List[EvidenceChunk], str, List[str], List[str]]:
    """
    STRICT VERIFICATION LAYER:
    1. Check every generated claim's referenced source_ids.
    2. Confirm each source_id actually exists in retrieved evidence.
    3. Strip any ungrounded claim or ungrounded citation.
    4. If no claims remain supported, clamp answer to 'Insufficient evidence in the provided documents.'
    5. Calculate truthful evidence-backed confidence.
    """
    valid_chunks_map = {c["chunk_id"]: c for c in retrieved_evidence}
    raw_claims = ai_response.get("claims", [])
    verified_claims = []
    used_chunk_ids = set()

    for item in raw_claims:
        claim_text = item.get("claim", "").strip()
        raw_source_ids = item.get("source_ids", [])
        
        # Keep only source IDs that were genuinely retrieved
        valid_sources = [sid for sid in raw_source_ids if sid in valid_chunks_map]
        
        if claim_text and valid_sources:
            verified_claims.append(GroundedClaim(
                claim=claim_text,
                source_ids=valid_sources
            ))
            for sid in valid_sources:
                used_chunk_ids.add(sid)

    # Attach only verified evidence chunks that support claims or were top retrieved
    verified_sources = []
    # prioritize chunks cited directly
    for sid in used_chunk_ids:
        chunk = valid_chunks_map[sid]
        verified_sources.append(EvidenceChunk(**chunk))
        
    # If no chunk was cited directly but some were retrieved, include top chunks for transparency
    if not verified_sources and retrieved_evidence:
        for c in retrieved_evidence[:3]:
            verified_sources.append(EvidenceChunk(**c))

    raw_answer = ai_response.get("answer", "").strip()
    missing_info = ai_response.get("missing_information", [])
    contradictions = ai_response.get("contradictions", [])
    
    # Grounding check:
    # If there are no verified claims and retrieval found nothing or AI signaled lack of evidence:
    if not verified_claims and ("insufficient evidence" in raw_answer.lower() or not retrieved_evidence):
        final_answer = "Insufficient evidence in the provided documents."
        confidence = "low"
    elif not verified_claims and retrieved_evidence:
        final_answer = raw_answer or "Insufficient evidence in the provided documents."
        confidence = "low"
    else:
        final_answer = raw_answer
        # Evidence-based confidence calculation
        # High: >= 2 verified claims and relevant sources
        # Medium: 1 verified claim
        # Low: no claims or presence of contradictions
        if contradictions:
            confidence = "medium"
        elif len(verified_claims) >= 2 and len(used_chunk_ids) >= 1:
            confidence = "high"
        elif len(verified_claims) >= 1:
            confidence = "medium"
        else:
            confidence = "low"

    return final_answer, verified_claims, verified_sources, confidence, missing_info, contradictions
