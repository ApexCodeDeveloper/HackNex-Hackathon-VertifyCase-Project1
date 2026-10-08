import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = None

def get_gemini_client():
    global _client
    if _client is not None:
        return _client
    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

STRICT_SYSTEM_PROMPT = """You are a grounded legal document intelligence assistant.
You may ONLY make factual claims that are supported directly by the supplied evidence chunks.
Do NOT use outside knowledge to fill missing information.
Do NOT invent facts, names, dates, amounts, case citations, or statutes.
Every factual claim MUST reference one or more supplied evidence chunk IDs.
If evidence is insufficient, say: "Insufficient evidence in the provided documents."
Never create a citation that does not correspond exactly to one of the supplied chunk IDs.

Output MUST be valid JSON:
{
  "answer": "Grounded answer text summarizing the findings or explaining lack of evidence",
  "claims": [
    {
      "claim": "Specific factual claim derived strictly from evidence",
      "source_ids": ["chunk_id_1"]
    }
  ],
  "confidence": "high" | "medium" | "low",
  "missing_information": [],
  "contradictions": []
}
"""

def generate_grounded_answer(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    if not evidence_chunks:
        return {
            "answer": "Insufficient evidence in the provided documents.",
            "claims": [],
            "confidence": "low",
            "missing_information": ["No relevant evidence found in the selected documents."],
            "contradictions": []
        }
        
    client = get_gemini_client()
    if not client:
        return {
            "answer": "AI analysis is temporarily unavailable. GEMINI_API_KEY is not configured.",
            "claims": [],
            "confidence": "low",
            "missing_information": ["Gemini API key is required for AI reasoning."],
            "contradictions": []
        }

    evidence_text = ""
    for chunk in evidence_chunks:
        evidence_text += f"\n--- EVIDENCE CHUNK [{chunk['chunk_id']}] ---\nDoc: {chunk['document_name']} (P.{chunk['page_number']})\n{chunk['text']}\n"

    history_text = ""
    if conversation_history:
        recent = conversation_history[-4:]
        history_text = "Prior conversation context:\n"
        for msg in recent:
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
        history_text += "\n"

    user_prompt = f"{history_text}EVIDENCE PROVIDED:\n{evidence_text}\nUSER QUESTION:\n{query}\n\nRespond strictly in the JSON format."

    try:
        response_text = _generate_with_retry(
            client, user_prompt, system_instruction=STRICT_SYSTEM_PROMPT
        )
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        return json.loads(response_text.strip())
    except Exception as e:
        return {
            "answer": "AI analysis error occurred while evaluating evidence.",
            "claims": [],
            "confidence": "low",
            "missing_information": [f"Backend error: {str(e)}"],
            "contradictions": []
        }

def _generate_with_retry(client, prompt: str, max_attempts: int = 3,
                         system_instruction: Optional[str] = None):
    """Call Gemini, retrying transient 503/429 errors with backoff.
    Returns response text, or an error dict if all attempts fail."""
    import time
    config_kwargs = {"response_mime_type": "application/json", "temperature": 0.0}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    last_error = None
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            err = str(e)
            # 429 RESOURCE_EXHAUSTED is a daily quota - retrying is futile and
            # would waste quota. Only retry transient server/load errors.
            transient = (("503" in err or "500" in err or "UNAVAILABLE" in err
                          or "disconnected" in err)
                         and "RESOURCE_EXHAUSTED" not in err
                         and "429" not in err)
            if transient and attempt < max_attempts - 1:
                time.sleep(2 * (attempt + 1))
                continue
            break
    raise last_error

def analyze_document_contradictions(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(chunks) < 2:
        return []
    client = get_gemini_client()
    if not client:
        return []

    evidence_text = ""
    for c in chunks:
        evidence_text += f"[CHUNK {c['chunk_id']}] Document: {c['document_name']}, Page: {c['page_number']}\n{c['text']}\n\n"

    prompt = f"""Examine these evidence passages from uploaded legal documents.
Identify genuine factual discrepancies or opposing claims.

EVIDENCE:
{evidence_text}

OUTPUT FORMAT JSON:
{{
  "contradictions": [
    {{
      "topic": "Brief topic title",
      "claim_a": {{
        "text": "Specific assertion in document A",
        "source": "Document A filename",
        "page": 1,
        "chunk_id": "chunk_id"
      }},
      "claim_b": {{
        "text": "Conflicting assertion in document B",
        "source": "Document B filename",
        "page": 2,
        "chunk_id": "chunk_id"
      }},
      "explanation": "Clear explanation of how they contradict"
    }}
  ]
}}

If no supported contradictions exist, return {{ "contradictions": [] }}. Never invent any."""

    try:
        response_text = _generate_with_retry(client, prompt)
        data = json.loads(response_text)
        return data.get("contradictions", [])
    except Exception as e:
        print(f"Contradiction error: {e}")
        return []

def review_case_documents(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not chunks:
        return {
            "key_facts": [],
            "contradictions": [],
            "missing_information": ["No documents provided."],
            "confidence": "low",
            "summary": "No evidence available."
        }
    client = get_gemini_client()
    if not client:
        return {
            "key_facts": [],
            "contradictions": [],
            "missing_information": ["Gemini API key is not configured."],
            "confidence": "low",
            "summary": "AI backend unavailable."
        }

    evidence_text = ""
    for c in chunks:
        evidence_text += f"[CHUNK {c['chunk_id']}] Doc: {c['document_name']}, P.{c['page_number']}\n{c['text']}\n\n"

    prompt = f"""Synthesize key supported facts, contradictions, and missing details from this evidence:
{evidence_text}

OUTPUT JSON:
{{
  "summary": "Concise factual summary",
  "key_facts": [{{"claim": "Supported fact", "source_ids": ["chunk_id"]}}],
  "contradictions": [
    {{
      "topic": "...",
      "claim_a": {{"text": "...", "source": "...", "page": 1, "chunk_id": "..."}},
      "claim_b": {{"text": "...", "source": "...", "page": 2, "chunk_id": "..."}},
      "explanation": "..."
    }}
  ],
  "missing_information": ["Evidentially missing detail"],
  "confidence": "high" | "medium" | "low"
}}"""
    try:
        response_text = _generate_with_retry(client, prompt)
        return json.loads(response_text)
    except Exception as e:
        return {
            "summary": f"Review error: {str(e)}",
            "key_facts": [],
            "contradictions": [],
            "missing_information": [str(e)],
            "confidence": "low"
        }


# Document types the drafting assistant knows how to structure.
DRAFT_DOC_TYPES = {
    "motion": "a court motion (caption, introduction, statement of facts, legal argument, conclusion, prayer for relief)",
    "memorandum": "an internal legal memorandum (question presented, brief answer, statement of facts, discussion/analysis, conclusion)",
    "demand_letter": "a formal demand letter (date, addressee, re line, statement of the matter, demand, deadline, reservation of rights)",
    "contract_clause": "a precise contract clause (defined terms, operative language, conditions, remedies)",
    "general": "a well-structured legal document appropriate to the instructions",
}

DRAFT_SYSTEM_PROMPT = """You are a grounded legal drafting assistant.
You may ONLY use facts that are directly supported by the supplied evidence chunks.
Do NOT invent facts, names, dates, amounts, case citations, statutes, parties, or jurisdiction.
Every factual assertion in the draft MUST be traceable to one or more supplied evidence chunk IDs.
If the evidence does not support a required element, state the gap explicitly in the draft and list it under missing_information — never fabricate it.
Add inline citation markers in the draft text using the exact form [chunk_id] after each supported statement.

Output MUST be valid JSON:
{
  "draft_text": "The full drafted document as plain text, with [chunk_id] markers after supported statements",
  "claims": [
    {"claim": "A supported factual statement used in the draft", "source_ids": ["chunk_id_1"]}
  ],
  "confidence": "high" | "medium" | "low",
  "missing_information": ["Element that could not be drafted because the evidence is silent"],
  "contradictions": []
}
Never reference a chunk ID that was not supplied."""


def draft_legal_document(
    query: str,
    evidence_chunks: List[Dict[str, Any]],
    doc_type: str = "general",
) -> Dict[str, Any]:
    """Draft a legal document grounded strictly in the supplied evidence.

    Returns a dict shaped like generate_grounded_answer so the existing
    verification layer can reuse it: {answer, claims, confidence,
    missing_information, contradictions}. The drafted text is returned under
    "answer" (rendered as draft_text by the API layer).
    """
    shape = DRAFT_DOC_TYPES.get(doc_type, DRAFT_DOC_TYPES["general"])

    if not evidence_chunks:
        return {
            "answer": "Insufficient evidence in the provided documents to draft this document.",
            "claims": [],
            "confidence": "low",
            "missing_information": ["No relevant evidence found in the selected documents."],
            "contradictions": [],
        }

    client = get_gemini_client()
    if not client:
        return {
            "answer": "AI analysis is temporarily unavailable. GEMINI_API_KEY is not configured.",
            "claims": [],
            "confidence": "low",
            "missing_information": ["Gemini API key is required for AI drafting."],
            "contradictions": [],
        }

    evidence_text = ""
    for chunk in evidence_chunks:
        evidence_text += (
            f"\n--- EVIDENCE CHUNK [{chunk['chunk_id']}] ---\n"
            f"Doc: {chunk['document_name']} (P.{chunk['page_number']})\n{chunk['text']}\n"
        )

    user_prompt = (
        f"Draft {shape}.\n\n"
        f"DRAFTING INSTRUCTIONS FROM USER:\n{query}\n\n"
        f"EVIDENCE PROVIDED (only these facts may be used):\n{evidence_text}\n\n"
        f"Respond strictly in the required JSON format."
    )

    try:
        response_text = _generate_with_retry(
            client, user_prompt, system_instruction=DRAFT_SYSTEM_PROMPT
        )
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        data = json.loads(response_text.strip())
        # Normalize to the grounded-answer shape the verifier expects.
        return {
            "answer": data.get("draft_text", ""),
            "claims": data.get("claims", []),
            "confidence": data.get("confidence", "medium"),
            "missing_information": data.get("missing_information", []),
            "contradictions": data.get("contradictions", []),
        }
    except Exception as e:
        return {
            "answer": "AI drafting error occurred while generating the document.",
            "claims": [],
            "confidence": "low",
            "missing_information": [str(e)],
            "contradictions": [],
        }
