import { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Database } from 'lucide-react';
import { uploadKnowledge } from '../lib/api';

const EXAMPLE_FILES = [
  'iphone16promax.txt',
  'huawei_mate70pro.txt',
  'xiaomi15pro.txt',
  'oppo_findx8pro.txt',
  'vivo_x200pro.txt',
];

interface Props {
  onUploaded: () => void;
}

export default function KnowledgePanel({ onUploaded }: Props) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setResult(null);
    try {
      const res = await uploadKnowledge(file);
      setResult({ ok: true, msg: `${res.filename}: ${res.msg}` });
      onUploaded();
    } catch (e: any) {
      setResult({ ok: false, msg: e.message || '上传失败' });
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = '';
  };

  return (
    <div className="bg-white border-t border-gray-200">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="flex items-center gap-2 mb-3">
          <Database size={15} className="text-brand-600" />
          <h3 className="text-sm font-semibold text-gray-700">知识库管理</h3>
        </div>

        <div className="flex items-start gap-4">
          {/* 上传区 */}
          <div className="shrink-0">
            <label className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium cursor-pointer transition-colors
              ${uploading
                ? 'bg-gray-50 border-gray-200 text-gray-400'
                : 'bg-brand-700 text-white border-brand-700 hover:bg-brand-800'
              }`}>
              {uploading ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Upload size={15} />
              )}
              {uploading ? '上传中...' : '上传 TXT 文件'}
              <input
                ref={fileRef}
                type="file"
                accept=".txt,text/plain"
                onChange={handleFileChange}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>

          {/* 结果 */}
          {result && (
            <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md ${
              result.ok
                ? 'bg-green-50 text-green-700 border border-green-100'
                : 'bg-red-50 text-red-600 border border-red-100'
            }`}>
              {result.ok ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
              {result.msg}
            </div>
          )}
        </div>

        {/* 示例文件 */}
        <div className="mt-3">
          <p className="text-[10px] text-gray-400 mb-1.5">知识库已有文档：</p>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_FILES.map((f) => (
              <span key={f} className="inline-flex items-center gap-1 text-[10px] text-gray-500 bg-gray-50 px-2 py-0.5 rounded border border-gray-100">
                <FileText size={10} className="text-brand-500" />
                {f}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
