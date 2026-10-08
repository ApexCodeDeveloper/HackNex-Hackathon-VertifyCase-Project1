// Types mirroring backend Pydantic models (backend/models.py)

export interface DocumentMetadata {
  document_id: string;
  document_name: string;
  file_size: number;
  page_count: number;
  chunk_count: number;
  created_at: string;
}

export interface EvidenceChunk {
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_id: string;
  text: string;
  relevance_score: number | null;
  section: string | null;
}

export interface GroundedClaim {
  claim: string;
  source_ids: string[];
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  claims: GroundedClaim[];
  sources: EvidenceChunk[];
  confidence: string;
  missing_information: string[];
  contradictions: string[];
}

export interface ChatMessageMeta {
  claims?: GroundedClaim[];
  sources?: EvidenceChunk[];
  confidence?: string;
  missing_information?: string[];
  contradictions?: string[];
}

export interface StoredMessage {
  message_id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  metadata: ChatMessageMeta | string | null;
  created_at: string;
}

export interface ConversationResponse {
  conversation_id: string;
  messages: StoredMessage[];
}

export interface ConversationListItem {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ContradictionClaim {
  text?: string;
  source?: string;
  page?: number;
  chunk_id?: string;
}

export interface ContradictionItem {
  topic: string;
  claim_a: ContradictionClaim;
  claim_b: ContradictionClaim;
  explanation: string;
}

export interface ContradictionsResponse {
  contradictions: ContradictionItem[];
  message: string | null;
}

export interface CaseReviewResponse {
  document_ids: string[];
  document_names: string[];
  key_facts: GroundedClaim[];
  sources: EvidenceChunk[];
  contradictions: ContradictionItem[];
  missing_information: string[];
  confidence: string;
  summary: string;
}

export type DraftDocType =
  | "motion"
  | "memorandum"
  | "demand_letter"
  | "contract_clause"
  | "general";

export interface DraftResponse {
  doc_type: DraftDocType;
  draft_text: string;
  claims: GroundedClaim[];
  sources: EvidenceChunk[];
  confidence: string;
  missing_information: string[];
  contradictions: string[];
}

export interface HealthResponse {
  status: string;
  backend: string;
  chroma_ready: boolean;
  gemini_configured: boolean;
  indexed_documents: number;
}

export interface StatsResponse {
  documents: number;
  chunks: number;
  conversations: number;
}
