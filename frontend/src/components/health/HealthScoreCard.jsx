import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertOctagon,
  HelpCircle,
  TrendingDown,
  Award,
  ChevronDown,
  ChevronUp,
  AlertTriangle
} from 'lucide-react';
import { statementApi } from '../../services/api';

export default function HealthScoreCard() {
  const [scoreData, setScoreData] = useState(null);
  const [distressData, setDistressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [whyModal, setWhyModal] = useState({ open: false, title: '', content: '' });

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    try {
      const [score, distress] = await Promise.all([
        statementApi.getHealthScore(),
        statementApi.getDistressSignals()
      ]);
      setScoreData(score);
      setDistressData(distress);
    } catch (err) {
      console.error("Failed to load health score:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !scoreData) return null;

  const { score, grade, components = [], is_preliminary, summary } = scoreData;
  const { signals = [], has_critical_distress } = distressData || {};

  const getScoreColor = (val) => {
    if (val >= 85) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (val >= 70) return 'text-indigo-400 border-indigo-500/40 bg-indigo-500/10';
    if (val >= 50) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className={`w-16 h-16 rounded-2xl border flex flex-col items-center justify-center font-bold ${getScoreColor(score)}`}>
            <span className="text-2xl leading-none">{score}</span>
            <span className="text-[10px] font-semibold uppercase tracking-wider mt-0.5">/ 100</span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white">Financial Health Score</h2>
              <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${getScoreColor(score)}`}>
                {grade}
              </span>
              {is_preliminary && (
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-800 text-slate-400 rounded-md">
                  Preliminary (&lt; 30 days)
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-xl">{summary}</p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 rounded-xl transition self-start sm:self-auto"
        >
          {expanded ? "Hide Component Math" : "View Transparent Breakdown"}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Early Distress Signals Banner */}
      {signals.length > 0 && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl space-y-3">
          <div className="flex items-center gap-2 text-rose-300 text-xs font-bold uppercase tracking-wider">
            <AlertOctagon className="w-4 h-4" />
            Early Financial Distress Signals Detected ({signals.length})
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {signals.map((sig, idx) => (
              <div key={idx} className="p-3 bg-slate-900/80 border border-rose-500/20 rounded-xl space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{sig.signal}</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 uppercase">
                    {sig.severity}
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 leading-tight">{sig.evidence}</p>
                <p className="text-[11px] text-emerald-400 font-medium pt-1">
                  💡 <strong>Action:</strong> {sig.remedy}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expanded Breakdown Table */}
      {expanded && (
        <div className="pt-2 border-t border-slate-800 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            Explainable Component Scoring Model (100 Max Points)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {components.map((c) => (
              <div key={c.component} className="bg-slate-800/40 border border-slate-700/60 p-4 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{c.component}</span>
                  <span className="text-xs font-mono font-bold text-indigo-400">
                    {c.points_awarded} / {c.max_points} pts
                  </span>
                </div>

                <div className="text-[11px] text-slate-300">
                  Measured Value: <strong className="text-white font-mono">{c.actual_value}</strong>
                </div>

                <p className="text-[11px] text-slate-400 leading-relaxed">{c.explanation}</p>

                <div className="pt-2 border-t border-slate-700/40">
                  <span className="text-[10px] text-slate-500 font-mono block truncate" title={c.calculation_method}>
                    Method: {c.calculation_method}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
