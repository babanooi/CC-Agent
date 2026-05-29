import { useState, useEffect, useCallback } from 'react';
import Toolbar from './components/Toolbar';
import SessionSidebar from './components/SessionSidebar';
import ChatPanel from './components/ChatPanel';
import DiagnosticsPanel from './components/DiagnosticsPanel';
import KnowledgePanel from './components/KnowledgePanel';
import {
  streamChat, streamChatImage, endSession, getSessionHistory,
  getUserProfile, listSessions, getHealth,
} from './lib/api';
import type {
  UIMessage, SessionSummary, UserProfile, HealthStatus,
} from './types';

function now() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export default function App() {
  // ---- 状态 ----
  const [userId, setUserId] = useState('default');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 左侧面板
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // 诊断（流式模式下只保留 session 和轮次信息）
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState('');
  const [lastResult, setLastResult] = useState<Record<string, any> | null>(null);

  // ---- 数据刷新 ----
  const refreshHealth = useCallback(async () => {
    try {
      setHealthError('');
      const h = await getHealth();
      setHealth(h);
    } catch (e: any) {
      setHealthError(e.message || '无法获取健康状态');
    }
  }, []);

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = await listSessions();
      setSessions(data.sessions);
    } catch {
      // 静默失败
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const refreshProfile = useCallback(async (uid: string) => {
    setProfileLoading(true);
    try {
      const p = await getUserProfile(uid);
      setProfile(p);
    } catch {
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, []);

  // 初始化
  useEffect(() => {
    refreshHealth();
    refreshSessions();
    refreshProfile(userId);
  }, []);

  const handleUserIdChange = (uid: string) => {
    setUserId(uid);
    refreshProfile(uid);
  };

  useEffect(() => {
    const timer = setInterval(refreshHealth, 30000);
    return () => clearInterval(timer);
  }, [refreshHealth]);

  // ---- 消息处理（流式）----
  const appendUserMessage = (text: string, imageCount = 0): UIMessage => ({
    id: `u-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: now(),
    imageCount,
  });

  // 纯文本发送（流式）
  const handleSendText = async (question: string) => {
    setError('');
    setLoading(true);

    const userMsg = appendUserMessage(question);
    const assistantId = `a-${Date.now()}`;
    const assistantPlaceholder: UIMessage = {
      id: assistantId, role: 'assistant', content: '', timestamp: now(),
    };
    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);

    let answer = '';
    try {
      const result = await streamChat(
        { question, session_id: sessionId, user_id: userId },
        (token) => {
          answer += token;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: answer } : m)),
          );
        },
      );

      // 从流末尾提取元数据
      const meta = result.meta || {};
      const sid = meta.session_id || sessionId;
      if (sid && sid !== sessionId) setSessionId(sid);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: result.text, intent: meta.intent, turnCount: meta.turn_count, verification: meta.verification }
            : m,
        ),
      );
      setLastResult({
        answer: result.text,
        intent: meta.intent,
        verification: meta.verification,
        session_id: sid,
        turn_count: meta.turn_count,
        image_desc: meta.image_desc,
        detected_products: meta.detected_products,
      });
    } catch (e: any) {
      setError(e.message || '请求失败');
      // 移除空占位
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setLoading(false);
      refreshSessions();
    }
  };

  // 图片发送（流式）
  const handleSendImage = async (question: string, files: File[]) => {
    setError('');
    setLoading(true);

    const userMsg = appendUserMessage(question, files.length);
    const assistantId = `a-${Date.now()}`;
    const assistantPlaceholder: UIMessage = {
      id: assistantId, role: 'assistant', content: '', timestamp: now(),
    };
    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);

    const form = new FormData();
    form.append('question', question);
    form.append('user_id', userId);
    if (sessionId) form.append('session_id', sessionId);
    files.forEach((f) => form.append('images', f));

    let answer = '';
    try {
      const result = await streamChatImage(form, (token) => {
        answer += token;
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: answer } : m)),
        );
      });

      const meta = result.meta || {};
      const sid = meta.session_id || sessionId;
      if (sid && sid !== sessionId) setSessionId(sid);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: result.text, intent: meta.intent, turnCount: meta.turn_count, verification: meta.verification }
            : m,
        ),
      );
      setLastResult({
        answer: result.text,
        intent: meta.intent,
        verification: meta.verification,
        session_id: sid,
        turn_count: meta.turn_count,
        image_desc: meta.image_desc,
        detected_products: meta.detected_products,
        image_count: files.length,
      });
    } catch (e: any) {
      setError(e.message || '请求失败');
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setLoading(false);
      refreshSessions();
    }
  };

  // 结束会话
  const handleEndSession = async () => {
    if (!sessionId) return;
    try {
      await endSession(sessionId, userId);
    } catch {
      // 即使失败也清空本地
    }
    setSessionId(null);
    setLastResult(null);
    refreshSessions();
    refreshProfile(userId);
  };

  // 清空界面
  const handleClearMessages = () => {
    setMessages([]);
    setLastResult(null);
    setError('');
  };

  // 选择历史会话
  const handleSelectSession = async (sid: string) => {
    try {
      const history = await getSessionHistory(sid);
      const uiMessages: UIMessage[] = history.messages.map((m, i) => ({
        id: `h-${sid}-${i}`,
        role: (m.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
        content: m.content,
        timestamp: '',
        imageCount: m.image_count || 0,
      }));
      setMessages(uiMessages);
      setSessionId(sid);
      setLastResult(null);
      setError('');
    } catch {
      // 静默失败
    }
  };

  const handleKnowledgeUploaded = () => {
    refreshHealth();
  };

  return (
    <div className="h-full flex flex-col">
      <Toolbar
        health={health}
        healthError={healthError}
        userId={userId}
        onRefresh={refreshHealth}
      />

      <div className="flex-1 flex min-h-0">
        <SessionSidebar
          userId={userId}
          onUserIdChange={handleUserIdChange}
          sessions={sessions}
          sessionsLoading={sessionsLoading}
          onRefreshSessions={refreshSessions}
          currentSessionId={sessionId}
          onSelectSession={handleSelectSession}
          profile={profile}
          profileLoading={profileLoading}
        />

        <ChatPanel
          messages={messages}
          sessionId={sessionId}
          userId={userId}
          loading={loading}
          error={error}
          onSendText={handleSendText}
          onSendImage={handleSendImage}
          onEndSession={handleEndSession}
          onClearMessages={handleClearMessages}
        />

        <DiagnosticsPanel
          health={health}
          healthError={healthError}
          lastIntent={lastResult?.intent ?? null}
          lastVerification={lastResult?.verification ?? null}
          lastTurnCount={lastResult?.turn_count ?? null}
          sessionId={sessionId}
          lastImageDesc={lastResult?.image_desc ?? null}
          lastDetectedProducts={lastResult?.detected_products ?? null}
        />
      </div>

      <KnowledgePanel onUploaded={handleKnowledgeUploaded} />
    </div>
  );
}
