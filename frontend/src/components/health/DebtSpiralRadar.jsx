import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, HelpCircle, Activity, Info } from 'lucide-react';
import { statementApi } from '../../services/api';

export default function DebtSpiralRadar() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [whyModalOpen, setWhyModalOpen] = useState(false);

  useEffect(() => {
    fetchRadar();
  }, []);

  const fetchRadar = async () => {
    try {
      const res = await statementApi.getRiskRadar();
      setData(res);
    } catch (err) {
      console.error("Debt spiral radar fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data || !data.has_data) {
    return null;
  }

  const {
    overall_risk_score = 0,
    max_possible_score = 100,
    risk_tier = 'Minimal Elevated Risk',
    active_signal_count = 0,
    indicators = [],
    mom_comparison = {},
    methodology,
    assumptions = {}
  } = data;

  const isHighRisk = overall_risk_score >= 50;
  const isModerateRisk = overall_risk_score >= 25;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className={`p-1.5 rounded-lg ${
              isHighRisk ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
              isModerateRisk ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
              'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}>
              <ShieldAlert className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-white">
              Debt-Spiral Risk Radar
            </h3>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
              isHighRisk ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
              isModerateRisk ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
              'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}>
              {risk_tier}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Multi-dimensional risk radar evaluating borrowing loops, penalty fees, balance floor decay, and fixed obligations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* MoM Comparison Pill */}
          {mom_comparison.score_delta !== undefined && mom_comparison.score_delta !== 0 && (
            <div className={`flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-semibold ${
              mom_comparison.score_delta > 0
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            }`}>
              {mom_comparison.score_delta > 0 ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              <span>{Math.abs(mom_comparison.score_delta)} pts vs last month</span>
            </div>
          )}

          <button
            onClick={() => setWhyModalOpen(true)}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            Methodology
          </button>
        </div>
      </div>

      {/* Aggregate Score Bar & Summary */}
      <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs text-slate-400 block">Elevated Risk Index</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className={`text-3xl font-extrabold font-mono ${
              isHighRisk ? 'text-rose-400' : isModerateRisk ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {overall_risk_score}
            </span>
            <span className="text-xs text-slate-500">/ 100 Risk Points</span>
            <span className="text-[11px] text-slate-400 ml-2">
              ({active_signal_count} elevated factor{active_signal_count === 1 ? '' : 's'} active)
            </span>
          </div>
        </div>

        <div className="text-xs text-slate-400 max-w-md">
          <p className="leading-relaxed">
            Lower points represent higher financial resilience. Elevated risk points highlight potential cash flow friction 
            and borrowing pressures requiring proactive restructuring.
          </p>
        </div>
      </div>

      {/* Indicators Grid: One Bar per Signal */}
      <div className="space-y-3.5">
        {indicators.map((ind) => {
          const isElevated = ind.score > 0;
          const barWidth = Math.min(100, Math.round((ind.score / ind.max_points) * 100));

          return (
            <div
              key={ind.id}
              className={`p-3.5 rounded-2xl border transition ${
                isElevated
                  ? 'bg-slate-950/80 border-amber-500/30'
                  : 'bg-slate-950/40 border-slate-800/60'
              }`}
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">{ind.name}</span>
                  <span className={`px-2 py-0.2 rounded-full text-[10px] font-bold ${
                    isElevated
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  }`}>
                    {isElevated ? `ELEVATED (+${ind.score} PTS)` : 'CLEAN (0 PTS)'}
                  </span>
                </div>

                <span className="font-mono text-slate-400 text-[11px]">
                  Max {ind.max_points} pts
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden my-2">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    ind.score >= 15
                      ? 'bg-rose-500'
                      : ind.score > 0
                      ? 'bg-amber-500'
                      : 'bg-emerald-500/40'
                  }`}
                  style={{ width: `${isElevated ? barWidth : 4}%` }}
                />
              </div>

              {/* Evidence line */}
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                <strong className="text-slate-300">Evidence:</strong> {ind.evidence}
              </p>
            </div>
          );
        })}
      </div>

      {/* Methodology Modal */}
      {whyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-indigo-400">
              <div className="p-2 bg-indigo-500/10 rounded-xl">
                <HelpCircle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Debt-Spiral Radar Methodology</h3>
                <p className="text-xs text-slate-400">Deterministic multi-factor stress evaluation</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {methodology}
            </p>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
              <strong className="text-slate-200 block">Monitored Penalty Keywords:</strong>
              <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                {(assumptions.penalty_keywords || []).map((k) => (
                  <span key={k} className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300">
                    {k}
                  </span>
                ))}
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic">
              Note: This radar computes transparent risk indicators based purely on statement patterns. It constitutes an early-warning signal, never a legal verdict.
            </p>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setWhyModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

