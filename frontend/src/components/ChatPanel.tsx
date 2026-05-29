import { useState, useRef, useEffect } from 'react';
import {
  Send, ImagePlus, X, Square, Trash2, Loader2,
} from 'lucide-react';
import type { UIMessage } from '../types';
import MessageBubble from './MessageBubble';

interface Props {
  messages: UIMessage[];
  sessionId: string | null;
  userId: string;
  loading: boolean;
  error: string;
  onSendText: (question: string) => Promise<void>;
  onSendImage: (question: string, files: File[]) => Promise<void>;
  onEndSession: () => void;
  onClearMessages: () => void;
}

export default function ChatPanel({
  messages,
  sessionId,
  userId,
  loading,
  error,
  onSendText,
  onSendImage,
  onEndSession,
  onClearMessages,
}: Props) {
  const [input, setInput] = useState('');
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;
    if (loading) return;

    setInput('');
    const files = [...imageFiles];
    setImageFiles([]);

    if (files.length > 0) {
      await onSendImage(text, files);
    } else {
      await onSendText(text);
    }

    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const total = imageFiles.length + files.length;
    if (total > 3) {
      alert('单次最多上传 3 张图片');
      return;
    }
    setImageFiles((prev) => [...prev, ...files]);
    e.target.value = '';
  };

  const removeImage = (i: number) => {
    setImageFiles((prev) => prev.filter((_, idx) => idx !== i));
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-gray-50/60">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <div className="text-4xl mb-3 opacity-30">&#9670;</div>
              <p className="text-sm font-medium text-gray-500">CloudAgent 智能客服</p>
              <p className="text-xs mt-1 text-gray-400">
                {sessionId ? `会话 ${sessionId}` : '输入问题开始对话'}
              </p>
            </div>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-400 pl-4 animate-fade-in-up">
            <Loader2 size={14} className="animate-spin" />
            <span>思考中...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-xs px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        <div ref={messagesEnd} />
      </div>

      {/* 输入区 */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        {/* 已选图片预览 */}
        {imageFiles.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2.5">
            {imageFiles.map((f, i) => (
              <div key={i} className="flex items-center gap-1 text-[11px] bg-brand-50 text-brand-700 px-2 py-1 rounded-md border border-brand-100">
                <ImagePlus size={11} />
                <span className="max-w-[80px] truncate">{f.name}</span>
                <button onClick={() => removeImage(i)} className="hover:text-red-500">
                  <X size={11} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* 图片上传 */}
          <label className="shrink-0 p-2 rounded-lg border border-gray-200 text-gray-400 hover:text-brand-600 hover:border-brand-300 cursor-pointer transition-colors bg-gray-50">
            <ImagePlus size={16} />
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {/* 文本输入 */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
            rows={1}
            disabled={loading}
            className="flex-1 resize-none text-sm px-3 py-2 border border-gray-200 rounded-lg
                       bg-gray-50 focus:outline-none focus:border-brand-500 focus:ring-1
                       focus:ring-brand-500/20 placeholder-gray-400 disabled:opacity-50
                       transition-colors min-h-[36px] max-h-[120px]"
          />

          {/* 发送 */}
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="shrink-0 p-2 rounded-lg bg-brand-700 text-white hover:bg-brand-800
                       disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>

        {/* 底部操作 */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-1.5">
            {sessionId && (
              <button
                onClick={onEndSession}
                className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-red-500 transition-colors px-1.5 py-0.5 rounded hover:bg-red-50"
              >
                <Square size={10} />
                结束会话
              </button>
            )}
            {messages.length > 0 && (
              <button
                onClick={onClearMessages}
                className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-gray-600 transition-colors px-1.5 py-0.5 rounded hover:bg-gray-100"
              >
                <Trash2 size={10} />
                清空界面
              </button>
            )}
          </div>

          {sessionId && (
            <span className="text-[10px] text-gray-400 font-mono">
              {sessionId}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
