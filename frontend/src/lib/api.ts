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

// ==================== 流式请求底层 ====================

export interface StreamResult {
  text: string;
  meta: Record<string, any> | null;
}

function parseStreamMeta(raw: string): StreamResult {
  const marker = /__CA_META__(\{.*?\})__CA_META_END__/s;
  const match = raw.match(marker);
  if (match) {
    try {
      const meta = JSON.parse(match[1]);
      const text = raw.replace(marker, '').trim();
      return { text, meta };
    } catch {
      // JSON 解析失败，放弃元数据
    }
  }
  return { text: raw.trim(), meta: null };
}

async function streamFetch(
  url: string,
  init: RequestInit,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<StreamResult> {
  const res = await fetch(url, { ...init, signal });
  if (!res.ok) {
    throw new Error(`[${res.status}] ${await res.text()}`);
  }
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let raw = '';
  let metaDetected = false;
  const MARKER = '__CA_META__';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    raw += chunk;

    if (!metaDetected) {
      const idx = raw.indexOf(MARKER);
      if (idx >= 0) {
        // 找到标记——只输出标记之前的内容
        const alreadySent = raw.length - chunk.length;
        const before = raw.substring(alreadySent, idx);
        if (before) onToken(before);
        metaDetected = true;
      } else {
        onToken(chunk);
      }
    }
  }
  return parseStreamMeta(raw);
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

/** 流式文本对话——逐 token 回调，返回文本+元数据 */
export async function streamChat(
  req: ChatRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<StreamResult> {
  return streamFetch(
    `${BASE}/chat/stream`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    },
    onToken,
    signal,
  );
}

/** 流式图片对话——逐 token 回调，返回文本+元数据 */
export async function streamChatImage(
  form: FormData,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<StreamResult> {
  return streamFetch(`${BASE}/chat/image/stream`, { method: 'POST', body: form }, onToken, signal);
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
