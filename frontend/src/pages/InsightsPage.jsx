import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  PieChart as PieIcon,
  TrendingDown,
  TrendingUp,
  ShieldCheck,
  HelpCircle,
  ArrowRight,
  DollarSign,
  PiggyBank,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  Lightbulb
} from 'lucide-react';
import { statementApi } from '../services/api';
import AskStatementPanel from '../components/chat/AskStatementPanel';
import LeakageDetectorPanel from '../components/leakage/LeakageDetectorPanel';

export default function InsightsPage() {
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState(null);
  const [whyModal, setWhyModal] = useState({ open: false, title: '', content: '' });

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await statementApi.getInsights();
      setInsights(data);
    } catch (err) {
      console.error("Failed to load insights:", err);
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

  if (loading && !insights) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Synthesizing Explainable AI Recommendations...</p>
        </div>
      </div>
    );
  }

  const {
    ai_overview = {},
    budget_50_30_20 = {},
    personalized_budget = [],
    recommendations = [],
    total_potential_monthly_savings = 0,
    total_potential_annual_savings = 0
  } = insights || {};

  const { needs, wants, savings } = budget_50_30_20;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            Explainable AI Financial Advisory
          </div>
          <h1 className="text-2xl font-bold text-white mt-0.5">Financial Insights & Recommendations</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            50/30/20 budget framework, personalized spending levers, and transparent actionable suggestions
          </p>
        </div>

        {total_potential_monthly_savings > 0 && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl px-4 py-2.5 text-right">
            <span className="text-[10px] text-emerald-400 uppercase font-bold block">
              Identified Savings Opportunity
            </span>
            <span className="text-base font-bold text-emerald-300 font-mono">
              +{formatINR(total_potential_monthly_savings)}/mo
            </span>
            <span className="text-[10px] text-slate-400 block font-mono">
              ({formatINR(total_potential_annual_savings)}/yr)
            </span>
          </div>
        )}
      </div>

      {/* Natural Language Statement Search & Query Engine */}
      <AskStatementPanel />

      {/* SECTION 1: Explainable AI Executive Summary */}
      {ai_overview.headline && (
        <div className="bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-500/30 rounded-3xl p-6 shadow-xl space-y-4 relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Executive Overview
              </span>
              <h2 className="text-lg font-bold text-white mt-1">{ai_overview.headline}</h2>
            </div>
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">
            {ai_overview.narrative}
          </p>

          {/* Key Takeaways Bullet List */}
          {ai_overview.key_takeaways && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2 border-t border-slate-800">
              {ai_overview.key_takeaways.map((point, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                  <span>{point}</span>
                </div>
              ))}
            </div>
          )}

          <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-2">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>{ai_overview.privacy_guarantee}</span>
          </div>
        </div>
      )}

      {/* SECTION 2: 50/30/20 Budget Model */}
      {needs && wants && savings && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <PieIcon className="w-5 h-5 text-indigo-400" />
                50/30/20 Budget Allocation Model
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Benchmark vs actual allocation across essential needs, discretionary wants, and retention
              </p>
            </div>

            <button
              onClick={() => setWhyModal({
                open: true,
                title: '50/30/20 Budget Model Methodology',
                content: 'The 50/30/20 rule divides net income into: 50% for Needs (rent, utilities, groceries, EMIs), 30% for Wants (dining out, shopping, subscriptions), and 20% for Savings and debt reduction. FinSight maps your transactions into these exact buckets to highlight allocation imbalances.'
              })}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              Why am I seeing this?
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Needs Card */}
            <div className="bg-slate-800/40 border border-slate-700/60 p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{needs.label}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  needs.status === 'Healthy'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {needs.status}
                </span>
              </div>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-2xl font-bold text-white">{needs.actual_pct}%</span>
                <span className="text-xs text-slate-400">Target: {needs.target_pct}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${needs.actual_pct <= 55 ? 'bg-indigo-500' : 'bg-amber-500'}`}
                  style={{ width: `${Math.min(100, needs.actual_pct)}%` }}
                />
              </div>
              <div className="text-[11px] text-slate-400 flex justify-between font-mono">
                <span>Actual: {formatINR(needs.actual_amount)}</span>
                <span>Target: {formatINR(needs.target_amount)}</span>
              </div>
            </div>

            {/* Wants Card */}
            <div className="bg-slate-800/40 border border-slate-700/60 p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{wants.label}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  wants.status === 'Healthy'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {wants.status}
                </span>
              </div>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-2xl font-bold text-white">{wants.actual_pct}%</span>
                <span className="text-xs text-slate-400">Target: {wants.target_pct}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${wants.actual_pct <= 32 ? 'bg-indigo-500' : 'bg-rose-500'}`}
                  style={{ width: `${Math.min(100, wants.actual_pct)}%` }}
                />
              </div>
              <div className="text-[11px] text-slate-400 flex justify-between font-mono">
                <span>Actual: {formatINR(wants.actual_amount)}</span>
                <span>Target: {formatINR(wants.target_amount)}</span>
              </div>
            </div>

            {/* Savings Card */}
            <div className="bg-slate-800/40 border border-slate-700/60 p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{savings.label}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  savings.status === 'On Track'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {savings.status}
                </span>
              </div>
              <div className="flex items-baseline justify-between font-mono">
                <span className="text-2xl font-bold text-emerald-400">{savings.actual_pct}%</span>
                <span className="text-xs text-slate-400">Target: {savings.target_pct}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${Math.min(100, savings.actual_pct)}%` }}
                />
              </div>
              <div className="text-[11px] text-slate-400 flex justify-between font-mono">
                <span>Actual: {formatINR(savings.actual_amount)}</span>
                <span>Target: {formatINR(savings.target_amount)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Financial Leakage & Cost Creep Radar */}
      <LeakageDetectorPanel />

      {/* SECTION 3: Actionable Financial Recommendations */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-400" />
            Tailored Financial Suggestions ({recommendations.length})
          </h3>
          <p className="text-xs text-slate-400">
            Actionable optimization steps calculated directly from your statement's transaction arithmetic
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendations.map(rec => (
            <div
              key={rec.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-sm space-y-4 transition flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    {rec.action_type}
                  </span>
                  {rec.potential_monthly_savings > 0 && (
                    <span className="font-mono text-xs font-bold text-emerald-400">
                      Save {formatINR(rec.potential_monthly_savings)}/mo
                    </span>
                  )}
                </div>

                <h4 className="text-base font-bold text-white">{rec.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{rec.description}</p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-mono">
                  {rec.category}
                </span>

                <button
                  onClick={() => setWhyModal({
                    open: true,
                    title: `Recommendation Evidence: ${rec.title}`,
                    content: rec.why
                  })}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  Why am I seeing this?
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 4: Personalized Category Spending Budget */}
      {personalized_budget.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <PiggyBank className="w-5 h-5 text-indigo-400" />
                Personalized Category Budget Baseline
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Suggested category targets applying realistic 15% efficiency buffers to discretionary categories
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-800/60 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3 text-right">Current Monthly Avg</th>
                  <th className="px-4 py-3 text-right">Suggested Target</th>
                  <th className="px-4 py-3 text-right">Potential Monthly Savings</th>
                  <th className="px-4 py-3">Strategy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {personalized_budget.map(item => (
                  <tr key={item.category} className="hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-white font-sans font-medium">{item.category}</td>
                    <td className="px-4 py-3 text-right text-slate-300">{formatINR(item.current_monthly_avg)}</td>
                    <td className="px-4 py-3 text-right text-indigo-400 font-semibold">{formatINR(item.suggested_target)}</td>
                    <td className="px-4 py-3 text-right text-emerald-400 font-bold">
                      {item.potential_monthly_savings > 0 ? `+${formatINR(item.potential_monthly_savings)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-sans text-[11px]">{item.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* "Why am I seeing this?" Modal */}
      {whyModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-indigo-400 mb-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl">
                <HelpCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">{whyModal.title}</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{whyModal.content}</p>
            <div className="flex justify-end mt-5">
              <button
                onClick={() => setWhyModal({ open: false, title: '', content: '' })}
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg"
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

