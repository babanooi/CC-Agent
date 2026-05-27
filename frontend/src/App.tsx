import { useState, useEffect, useCallback } from 'react';
import Toolbar from './components/Toolbar';
import SessionSidebar from './components/SessionSidebar';
import ChatPanel from './components/ChatPanel';
import DiagnosticsPanel from './components/DiagnosticsPanel';
import KnowledgePanel from './components/KnowledgePanel';
import {
  sendChat, sendChatImage, endSession, getSessionHistory,
  getUserProfile, listSessions, getHealth,
} from './lib/api';
import type {
  UIMessage, ChatResponse, SessionSummary, UserProfile, HealthStatus,
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

  // 诊断
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState('');
  const [lastResult, setLastResult] = useState<ChatResponse | null>(null);

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

  // 用户 ID 变化时刷新
  const handleUserIdChange = (uid: string) => {
    setUserId(uid);
    refreshProfile(uid);
  };

  // 定时健康检查
  useEffect(() => {
    const timer = setInterval(refreshHealth, 30000);
    return () => clearInterval(timer);
  }, [refreshHealth]);

  // ---- 消息处理 ----
  const appendUserMessage = (text: string, imageCount = 0): UIMessage => ({
    id: `u-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: now(),
    imageCount,
  });

  const handleResponse = (res: ChatResponse) => {
    const assistantMsg: UIMessage = {
      id: `a-${Date.now()}`,
      role: 'assistant',
      content: res.answer,
      timestamp: now(),
      intent: res.intent,
      verification: res.verification,
      turnCount: res.turn_count,
      imageDesc: res.image_desc,
      detectedProducts: res.detected_products,
    };
    setMessages((prev) => [...prev, assistantMsg]);
    setSessionId(res.session_id);
    setLastResult(res);
  };

  // 纯文本发送
  const handleSendText = async (question: string): Promise<ChatResponse | null> => {
    setError('');
    setLoading(true);
    const userMsg = appendUserMessage(question);
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await sendChat({ question, session_id: sessionId, user_id: userId });
      handleResponse(res);
      refreshSessions();
      return res;
    } catch (e: any) {
      setError(e.message || '请求失败');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // 图片发送
  const handleSendImage = async (question: string, files: File[]): Promise<ChatResponse | null> => {
    setError('');
    setLoading(true);
    const userMsg = appendUserMessage(question, files.length);
    setMessages((prev) => [...prev, userMsg]);

    try {
      const form = new FormData();
      form.append('question', question);
      form.append('user_id', userId);
      if (sessionId) form.append('session_id', sessionId);
      files.forEach((f) => form.append('images', f));

      const res = await sendChatImage(form);
      handleResponse(res);
      refreshSessions();
      return res;
    } catch (e: any) {
      setError(e.message || '请求失败');
      return null;
    } finally {
      setLoading(false);
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

  // 清空界面（不删后端数据）
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

  // 上传知识后刷新
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
