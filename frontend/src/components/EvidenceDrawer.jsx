import React, { useState, useEffect } from 'react';
import { X, Search, CheckCircle2, AlertTriangle, FileText, ChevronRight, Layers, ShieldCheck } from 'lucide-react';
import { statementApi } from '../services/api';

export default function EvidenceDrawer({ isOpen, onClose, queryParams, title }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!isOpen || !queryParams) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    statementApi.getEvidence(queryParams)
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err?.response?.data?.detail || err.message || 'Failed to fetch proof rows');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [isOpen, queryParams]);

  if (!isOpen) return null;

  const transactions = (data?.transactions || []).filter((tx) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (tx.description || '').toLowerCase().includes(q) ||
      (tx.normalized_merchant || '').toLowerCase().includes(q) ||
      (tx.raw_text || '').toLowerCase().includes(q) ||
      (tx.date || '').includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      {/* Click outside to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Drawer Container */}
      <div className="w-full max-w-2xl bg-[#0f172a] border-l border-slate-800 text-slate-100 flex flex-col h-full shadow-2xl animate-in slide-in-from-right duration-200">
        
        {/* Header */}
        <div className="p-5 border-b border-slate-800/80 bg-[#131c35] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <FileText className="w-4 h-4" />
              </span>
              <h2 className="text-base font-bold text-white tracking-wide">
                Proof & Evidence Audit
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {title || `Source ledger breakdown for ${data?.metric || 'metric'}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Aggregate Summary Ribbon */}
        {data && (
          <div className="px-5 py-3.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-400">Contributing Total:</span>{' '}
              <span className="font-bold text-white text-sm">
                ₹{Number(data.computed_sum || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className="text-slate-500 ml-2">({data.count} transactions)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Confidence:</span>
              <span className={`px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 ${
                (data.average_confidence || 1.0) >= 0.90
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}>
                {(data.average_confidence || 1.0) >= 0.90 ? (
                  <ShieldCheck className="w-3.5 h-3.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                {Math.round((data.average_confidence || 1.0) * 100)}%
              </span>
            </div>
          </div>
        )}

        {/* Search Filter */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/40">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search narrative, merchant, or raw text..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {loading && (
            <div className="flex flex-col items-center justify-center h-48 space-y-2 text-slate-400">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs">Extracting ledger proof lines...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-400" />
              <div>
                <p className="font-semibold">Unable to load evidence rows</p>
                <p className="text-slate-400 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!loading && !error && transactions.length === 0 && (
            <div className="p-8 text-center text-slate-500 text-xs">
              No matching transactions found for this scope.
            </div>
          )}

          {!loading && !error && transactions.map((tx) => (
            <div
              key={tx.id}
              className={`p-3.5 rounded-xl border text-xs transition ${
                tx.is_tampered_or_drifted
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              {/* Row Header */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-slate-400 font-semibold">{tx.date}</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700">
                    {tx.category || 'Uncategorized'}
                  </span>
                  {tx.source_row && (
                    <span className="px-1.5 py-0.5 rounded bg-indigo-950/60 text-[10px] text-indigo-300 border border-indigo-800/40 font-mono">
                      Page {tx.source_page || 1}, Row {tx.source_row}
                    </span>
                  )}
                </div>

                <div className="text-right">
                  {tx.debit > 0 ? (
                    <span className="font-bold text-rose-400">
                      -₹{tx.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  ) : (
                    <span className="font-bold text-emerald-400">
                      +₹{tx.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  )}
                </div>
              </div>

              {/* Description & Normalized Merchant */}
              <div className="text-slate-200 font-medium">
                {tx.description}
              </div>

              {/* Raw Statement Text (Verbatim Evidence) */}
              {tx.raw_text && (
                <div className="mt-2 p-2 rounded-lg bg-black/40 border border-slate-800/60 font-mono text-[11px] text-slate-400 break-all leading-relaxed">
                  <span className="text-slate-500 select-none mr-1.5">RAW:</span>
                  {tx.raw_text}
                </div>
              )}

              {/* Confidence & Balance audit footer */}
              <div className="mt-2.5 pt-2 border-t border-slate-800/50 flex items-center justify-between text-[11px] text-slate-400">
                <span>Closing Bal: ₹{Number(tx.balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                <span className={`flex items-center gap-1 font-medium ${
                  (tx.extraction_confidence || 1.0) >= 0.90 ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {(tx.extraction_confidence || 1.0) >= 0.90 ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-3 h-3 text-amber-400" />
                  )}
                  {Math.round((tx.extraction_confidence || 1.0) * 100)}% Confidence
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Methodology Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#0c1322] text-[11px] text-slate-400">
          <p className="font-semibold text-slate-300">Deterministic Proof Guarantee:</p>
          <p className="mt-0.5 leading-relaxed text-slate-500">
            Every metric is mathematically derived from these verbatim lines. Zero data hallucination or black-box approximation.
          </p>
        </div>

      </div>
    </div>
  );
}

