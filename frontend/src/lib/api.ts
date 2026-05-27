import type {
  ChatRequest,
  ChatResponse,
  SessionSummary,
  SessionHistory,
  UserProfile,
  HealthStatus,
  KnowledgeUploadResponse,
} from '../types';

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`[${res.status}] ${body || res.statusText}`);
  }
  return res.json();
}

// ==================== 对话 ====================

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function sendChatImage(form: FormData): Promise<ChatResponse> {
  return request<ChatResponse>('/chat/image', {
    method: 'POST',
    body: form,
  });
}

export function chatStreamUrl(): string {
  return `${BASE}/chat/stream`;
}

export async function endSession(sessionId: string, userId: string): Promise<{ msg: string }> {
  return request(`/chat/${sessionId}/end?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
  });
}

export async function getSessionHistory(sessionId: string): Promise<SessionHistory> {
  return request(`/chat/${sessionId}/history`);
}

// ==================== 知识库 ====================

export async function uploadKnowledge(file: File): Promise<KnowledgeUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  return request<KnowledgeUploadResponse>('/knowledge/upload', {
    method: 'POST',
    body: form,
  });
}

// ==================== 用户 & 会话 ====================

export async function getUserProfile(userId: string): Promise<UserProfile> {
  return request(`/users/${encodeURIComponent(userId)}/profile`);
}

export async function listSessions(): Promise<{ sessions: SessionSummary[] }> {
  return request('/users/sessions');
}

// ==================== 健康检查 ====================

export async function getHealth(): Promise<HealthStatus> {
  return request('/health');
}
