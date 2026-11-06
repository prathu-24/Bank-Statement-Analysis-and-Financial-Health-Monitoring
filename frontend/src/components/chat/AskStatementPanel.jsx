import React, { useState } from 'react';
import {
  MessageSquare,
  Search,
  Sparkles,
  Database,
  ArrowRight,
  HelpCircle,
  FileText,
  CornerDownLeft,
  CheckCircle2,
  Cpu
} from 'lucide-react';
import { statementApi } from '../../services/api';

const SAMPLE_PROMPTS = [
  "What is my biggest expense?",
  "How much did I spend on Food & Dining?",
  "What was my highest balance?",
  "What was my lowest balance?",
  "How much did I spend on Swiggy?",
  "What was my total verified income?"
];

export default function AskStatementPanel() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAsk = async (queryToAsk) => {
    const q = queryToAsk || question;
    if (!q || !q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await statementApi.askStatement(q.trim());
      setResult(res);
      if (queryToAsk) setQuestion(queryToAsk);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to process query");
    } finally {
      setLoading(false);
    }
  };

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-white">
              Ask Your Statement
            </h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 uppercase">
              Deterministic Query Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Plain-English inquiry translated into a secure Structured Query Spec. Evaluated locally via Pandas with 100% source provenance.
          </p>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span>Zero Raw SQL &bull; Local Execution</span>
        </div>
      </div>

      {/* Query Input Box */}
      <div className="space-y-3">
        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAsk();
            }}
            placeholder="e.g., 'How much did I spend on Food?' or 'What was my highest balance?'"
            className="w-full bg-slate-950/80 border border-slate-800 rounded-2xl py-3 pl-4 pr-24 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="absolute right-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition shadow-md shadow-indigo-600/20"
          >
            {loading ? "Evaluating..." : "Ask"}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] text-slate-500 font-medium">Try:</span>
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleAsk(prompt)}
              className="text-[11px] px-2.5 py-1 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 transition"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="space-y-4 pt-2 border-t border-slate-800">
          {/* Answer Card */}
          <div className="p-4 bg-slate-950/70 border border-indigo-500/30 rounded-2xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                Computed Statement Answer
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                Engine: {result.engine_used}
              </span>
            </div>
            <p className="text-sm font-semibold text-white leading-relaxed">
              {result.answer}
            </p>
          </div>

          {/* Structured Query Spec Inspector (Transparent Architecture) */}
          <div className="p-3.5 bg-slate-950/40 border border-slate-800/80 rounded-2xl space-y-2 text-xs">
            <div className="flex items-center justify-between text-slate-300 font-semibold text-[11px]">
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Parsed Structured Query Spec (Safe Execution)
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Zero SQL Injection Surface</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px]">
              <div className="bg-slate-900/60 p-2 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Intent</span>
                <span className="text-indigo-300 font-bold truncate block">{result.structured_spec?.intent || 'search'}</span>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Filter Merchant</span>
                <span className="text-white font-bold truncate block">{result.structured_spec?.merchant || 'Any'}</span>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Filter Category</span>
                <span className="text-white font-bold truncate block">{result.structured_spec?.category || 'Any'}</span>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Metric / Aggregation</span>
                <span className="text-emerald-400 font-bold truncate block">{result.structured_spec?.metric?.toUpperCase() || 'SUM'}</span>
              </div>
            </div>
          </div>

          {/* Supporting Evidence Source Rows Table */}
          {result.source_rows && result.source_rows.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <div className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  Contributing Statement Rows ({result.source_count} Total)
                </div>
                <span className="text-[10px] text-slate-500 font-mono">Row-level Audit Provenance</span>
              </div>

              <div className="max-h-56 overflow-y-auto border border-slate-800 rounded-2xl bg-slate-950/60">
                <table className="w-full text-[11px] text-left">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px] sticky top-0">
                    <tr>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Description</th>
                      <th className="py-2 px-3">Category</th>
                      <th className="py-2 px-3 text-right">Debit</th>
                      <th className="py-2 px-3 text-right">Credit</th>
                      <th className="py-2 px-3 text-right">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.source_rows.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-900/40 text-slate-300 font-mono">
                        <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{row.date}</td>
                        <td className="py-2 px-3 text-white truncate max-w-[200px]">{row.description}</td>
                        <td className="py-2 px-3 text-slate-400">{row.category}</td>
                        <td className="py-2 px-3 text-right text-rose-400">
                          {row.debit > 0 ? formatINR(row.debit) : '-'}
                        </td>
                        <td className="py-2 px-3 text-right text-emerald-400">
                          {row.credit > 0 ? formatINR(row.credit) : '-'}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-300">{formatINR(row.balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

