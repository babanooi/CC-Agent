import { Bot, User, Image, Tag, CheckCircle, AlertTriangle } from 'lucide-react';
import type { UIMessage } from '../types';

const INTENT_LABELS: Record<string, string> = {
  product_query: '产品查询',
  product_compare: '产品对比',
  troubleshoot: '故障排查',
  purchase_advice: '购买建议',
  chitchat: '闲聊',
};

interface Props {
  message: UIMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 animate-fade-in-up ${isUser ? 'justify-end' : ''}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-md bg-brand-700 flex items-center justify-center shrink-0 mt-0.5">
          <Bot size={14} className="text-white" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
        {/* 用户消息 */}
        {isUser ? (
          <div className="bg-accent-600 text-white text-sm px-3.5 py-2.5 rounded-2xl rounded-tr-md inline-block">
            {message.imageCount ? (
              <div className="flex items-center gap-1.5 mb-1 text-white/70 text-xs">
                <Image size={12} />
                <span>附图 {message.imageCount} 张</span>
              </div>
            ) : null}
            {message.content}
          </div>
        ) : (
          /* 助手消息 */
          <div className="space-y-2">
            <div className="bg-white border border-gray-200 text-sm text-gray-700 px-4 py-3 rounded-2xl rounded-tl-md shadow-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>

            {/* 元信息卡片 */}
            <div className="flex flex-wrap gap-1.5 text-[10px]">
              {message.intent && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full border border-purple-100">
                  <Tag size={9} />
                  {INTENT_LABELS[message.intent.intent] || message.intent.intent}
                  {message.intent.confidence != null && (
                    <span className="opacity-60 ml-0.5">
                      {(message.intent.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </span>
              )}

              {message.turnCount != null && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-50 text-gray-500 rounded-full border border-gray-100">
                  第 {message.turnCount} 轮
                </span>
              )}

              {message.verification && (
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border ${
                  message.verification.pass !== false
                    ? 'bg-green-50 text-green-600 border-green-100'
                    : 'bg-red-50 text-red-600 border-red-100'
                }`}>
                  {message.verification.pass !== false ? (
                    <CheckCircle size={9} />
                  ) : (
                    <AlertTriangle size={9} />
                  )}
                  验证{message.verification.score != null ? `  ${message.verification.score}分` : ''}
                </span>
              )}
            </div>

            {/* 图片识别信息 */}
            {message.imageDesc && (
              <div className="text-[11px] text-gray-500 bg-gray-50 px-2.5 py-1.5 rounded-md border border-gray-100">
                <span className="text-gray-400">图片识别：</span>
                {message.imageDesc}
                {message.detectedProducts && message.detectedProducts.length > 0 && (
                  <span className="ml-1.5 text-brand-600">
                    检测到：{message.detectedProducts.join('、')}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* 时间戳 */}
        <div className={`text-[10px] text-gray-300 mt-0.5 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp}
        </div>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-md bg-accent-500 flex items-center justify-center shrink-0 mt-0.5">
          <User size={14} className="text-white" />
        </div>
      )}
    </div>
  );
}
