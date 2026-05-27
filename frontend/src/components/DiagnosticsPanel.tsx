import { Activity, FileText, Cpu, Image, Smartphone } from 'lucide-react';
import type { HealthStatus, VerificationInfo, IntentInfo } from '../types';

interface Props {
  health: HealthStatus | null;
  healthError: string;
  lastIntent: IntentInfo | null;
  lastVerification: VerificationInfo | null;
  lastTurnCount: number | null;
  sessionId: string | null;
  lastImageDesc: string | null;
  lastDetectedProducts: string[] | null;
}

function Empty({ text }: { text: string }) {
  return <span className="text-gray-400 text-[11px]">{text}</span>;
}

function SectionTitle({ icon: Icon, label }: { icon: React.ComponentType<{ size?: number }>; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 mb-2 font-medium">
      <Icon size={10} />
      {label}
    </div>
  );
}

export default function DiagnosticsPanel({
  health, healthError, lastIntent, lastVerification,
  lastTurnCount, sessionId, lastImageDesc, lastDetectedProducts,
}: Props) {
  return (
    <aside className="w-72 shrink-0 bg-white border-l border-gray-200 flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
          <Activity size={13} />
          诊断面板
        </h3>
        <p className="text-[10px] text-gray-400 mt-0.5">最近一次回答的详细信息</p>
      </div>

      <div className="p-4 space-y-5">
        {/* 意图 */}
        <section>
          <SectionTitle icon={Cpu} label="意图" />
          {lastIntent ? (
            <div className="space-y-1 text-[11px]">
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">类型</span>
                <span className="font-mono text-purple-600 font-medium">{lastIntent.intent}</span>
              </div>
              {lastIntent.confidence != null && (
                <div className="flex justify-between py-0.5">
                  <span className="text-gray-500">置信度</span>
                  <span className="font-mono text-gray-700">
                    {(lastIntent.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          ) : <Empty text="暂无意图数据" />}
        </section>

        {/* 验证 */}
        <section>
          <SectionTitle icon={FileText} label="验证结果" />
          {lastVerification ? (
            <div className="bg-gray-50 rounded-md p-2.5">
              <pre className="text-[10px] font-mono text-gray-600 whitespace-pre-wrap leading-relaxed">
                {JSON.stringify(lastVerification, null, 1)}
              </pre>
            </div>
          ) : <Empty text="暂无验证数据" />}
        </section>

        {/* 轮次 & 会话 */}
        <section>
          <SectionTitle icon={Activity} label="会话信息" />
          <div className="space-y-1 text-[11px]">
            {lastTurnCount != null && (
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">当前轮次</span>
                <span className="font-mono text-brand-700 font-medium">{lastTurnCount}</span>
              </div>
            )}
            {sessionId && (
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">会话 ID</span>
                <span className="font-mono text-gray-600 text-[10px]">{sessionId}</span>
              </div>
            )}
          </div>
        </section>

        {/* 图片识别 */}
        <section>
          <SectionTitle icon={Image} label="图片识别" />
          {lastImageDesc ? (
            <div className="space-y-2">
              <p className="text-[11px] text-gray-600 bg-gray-50 rounded p-2 leading-relaxed">{lastImageDesc}</p>
            </div>
          ) : <Empty text="暂无图片数据" />}
          {lastDetectedProducts && lastDetectedProducts.length > 0 && (
            <div className="mt-2">
              <SectionTitle icon={Smartphone} label="检测产品" />
              <div className="flex flex-wrap gap-1 mt-1">
                {lastDetectedProducts.map((p, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-brand-50 text-brand-700 rounded text-[10px] border border-brand-100">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* 系统状态 */}
        <section>
          <SectionTitle icon={Cpu} label="系统状态" />
          {healthError ? (
            <div className="text-[11px] text-red-500 bg-red-50 rounded p-2">{healthError}</div>
          ) : health ? (
            <div className="space-y-1 text-[11px]">
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">状态</span>
                <span className={`font-medium ${health.status === 'healthy' ? 'text-green-600' : 'text-red-500'}`}>
                  {health.status}
                </span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">BM25 文档</span>
                <span className="font-mono text-gray-700">{health.bm25_docs}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span className="text-gray-500">活跃会话</span>
                <span className="font-mono text-gray-700">{health.active_sessions}</span>
              </div>
            </div>
          ) : (
            <Empty text="加载中..." />
          )}
        </section>
      </div>
    </aside>
  );
}
