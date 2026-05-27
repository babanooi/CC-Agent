import { useState } from 'react';
import {
  Users, RefreshCw, ChevronRight, User, Calendar, MessageSquare,
  Sparkles, Smartphone, AlertCircle,
} from 'lucide-react';
import type { SessionSummary, UserProfile } from '../types';

interface Props {
  userId: string;
  onUserIdChange: (id: string) => void;
  sessions: SessionSummary[];
  sessionsLoading: boolean;
  onRefreshSessions: () => void;
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  profile: UserProfile | null;
  profileLoading: boolean;
}

export default function SessionSidebar({
  userId,
  onUserIdChange,
  sessions,
  sessionsLoading,
  onRefreshSessions,
  currentSessionId,
  onSelectSession,
  profile,
  profileLoading,
}: Props) {
  const [inputVal, setInputVal] = useState(userId);

  const handleBlur = () => {
    if (inputVal.trim()) onUserIdChange(inputVal.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputVal.trim()) {
      onUserIdChange(inputVal.trim());
    }
  };

  const profileData = profile?.data;
  const hasProfile = profileData && (Object.keys(profileData.profile).length > 0 || profileData.preferences.length > 0);

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-gray-200 flex flex-col h-full overflow-hidden">
      {/* 用户 ID */}
      <div className="p-3 border-b border-gray-100">
        <label className="text-[10px] uppercase tracking-widest text-gray-400 mb-1 block font-medium">
          用户 ID
        </label>
        <div className="flex gap-1.5">
          <input
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            className="flex-1 text-xs px-2.5 py-1.5 border border-gray-200 rounded-md bg-gray-50
                       focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20
                       font-mono text-gray-600 transition-colors"
            placeholder="default"
          />
        </div>
      </div>

      {/* 活跃会话 */}
      <div className="p-3 border-b border-gray-100 flex-1 overflow-hidden flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-2">
          <label className="text-[10px] uppercase tracking-widest text-gray-400 font-medium flex items-center gap-1">
            <Users size={11} />
            活跃会话
          </label>
          <button
            onClick={onRefreshSessions}
            className="text-gray-300 hover:text-gray-500 transition-colors"
            title="刷新"
          >
            <RefreshCw size={12} className={sessionsLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto -mx-1 px-1 space-y-0.5">
          {sessionsLoading && sessions.length === 0 ? (
            <div className="text-[11px] text-gray-400 py-4 text-center">加载中...</div>
          ) : sessions.length === 0 ? (
            <div className="text-[11px] text-gray-400 py-4 text-center">暂无活跃会话</div>
          ) : (
            sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => onSelectSession(s.session_id)}
                className={`w-full text-left px-2.5 py-2 rounded-md text-xs transition-colors flex items-center justify-between group
                  ${currentSessionId === s.session_id
                    ? 'bg-brand-50 text-brand-700 border border-brand-200'
                    : 'hover:bg-gray-50 text-gray-600 border border-transparent'
                  }`}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <MessageSquare size={11} className="shrink-0" />
                  <span className="truncate font-mono text-[11px]">{s.session_id}</span>
                </div>
                <span className="text-[10px] text-gray-400 shrink-0 ml-1.5">
                  {s.turn_count}轮
                </span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* 用户画像 */}
      <div className="p-3 border-t border-gray-100">
        <label className="text-[10px] uppercase tracking-widest text-gray-400 mb-2 block font-medium flex items-center gap-1">
          <User size={11} />
          用户画像
        </label>

        {profileLoading ? (
          <div className="text-[11px] text-gray-400 py-2">加载中...</div>
        ) : !hasProfile ? (
          <div className="text-[11px] text-gray-400 py-2">暂无画像数据</div>
        ) : (
          <div className="space-y-2 text-[11px]">
            {Object.keys(profileData.profile).length > 0 && (
              <div>
                <div className="text-[10px] text-gray-400 mb-0.5 font-medium">属性</div>
                {Object.entries(profileData.profile).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-[11px] py-0.5">
                    <span className="text-gray-500">{k}</span>
                    <span className="text-gray-700 font-medium">{v}</span>
                  </div>
                ))}
              </div>
            )}
            {profileData.preferences.length > 0 && (
              <div>
                <div className="text-[10px] text-gray-400 mb-1 font-medium flex items-center gap-1">
                  <Sparkles size={10} />偏好
                </div>
                <div className="flex flex-wrap gap-1">
                  {profileData.preferences.map((p, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded text-[10px]">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {profileData.mentioned_products.length > 0 && (
              <div>
                <div className="text-[10px] text-gray-400 mb-1 font-medium flex items-center gap-1">
                  <Smartphone size={10} />关注产品
                </div>
                <div className="flex flex-wrap gap-1">
                  {profileData.mentioned_products.map((p, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-brand-50 text-brand-700 rounded text-[10px]">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="text-[10px] text-gray-400 flex items-center gap-1">
              <Calendar size={10} />
              互动 {profileData.interaction_count} 次
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
