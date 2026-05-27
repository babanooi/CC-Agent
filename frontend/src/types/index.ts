// ==================== API 请求/响应类型 ====================

export interface ChatRequest {
  question: string;
  session_id?: string | null;
  user_id: string;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  turn_count: number;
  intent: IntentInfo;
  verification: VerificationInfo;
  image_desc?: string;
  detected_products?: string[];
}

export interface IntentInfo {
  intent: string;
  confidence?: number;
}

export interface VerificationInfo {
  pass?: boolean;
  score?: number;
  reason?: string;
  suggestion?: string;
}

export interface SessionSummary {
  session_id: string;
  user_id: string;
  turn_count: number;
  created_at: string;
}

export interface MessageRecord {
  role: string;
  content: string;
  image_count?: number;
}

export interface SessionHistory {
  session_id: string;
  messages: MessageRecord[];
  summary: string;
}

export interface UserProfile {
  user_id: string;
  data: {
    profile: Record<string, string>;
    preferences: string[];
    mentioned_products: string[];
    session_summaries: Array<{ summary: string; time: string }>;
    interaction_count: number;
  };
}

export interface HealthStatus {
  status: string;
  bm25_docs: number;
  active_sessions: number;
}

export interface KnowledgeUploadResponse {
  msg: string;
  filename: string;
}

// ==================== 前端内部类型 ====================

export interface UIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  imageCount?: number;
  intent?: IntentInfo;
  verification?: VerificationInfo;
  turnCount?: number;
  imageDesc?: string;
  detectedProducts?: string[];
}
