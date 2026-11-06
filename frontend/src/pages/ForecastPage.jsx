import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Calendar,
  AlertOctagon,
  HelpCircle,
  ShieldAlert,
  ArrowRight,
  DollarSign,
  Layers,
  Sparkles,
  Info,
  ShieldCheck,
  Activity,
  History
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import { statementApi } from '../services/api';
import HealthScoreCard from '../components/health/HealthScoreCard';

export default function ForecastPage() {
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState(null);
  const [horizonDays, setHorizonDays] = useState(30);
  const [viewMode, setViewMode] = useState('PROBABILISTIC'); // 'PROBABILISTIC' or 'DETERMINISTIC'
  const [whyModal, setWhyModal] = useState({ open: false, title: '', content: '' });

  useEffect(() => {
    fetchForecast(horizonDays);
  }, [horizonDays]);

  const fetchForecast = async (days) => {
    setLoading(true);
    try {
      const data = await statementApi.getCashFlowForecast(days);
      setForecast(data);
    } catch (err) {
      console.error("Forecast fetch error:", err);
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

  if (loading && !forecast) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Simulating 30-Day Liquidity Trajectory...</p>
        </div>
      </div>
    );
  }

  const {
    starting_balance = 0,
    ending_projected_balance = 0,
    total_projected_inflow = 0,
    total_projected_outflow = 0,
    daily_projection = [],
    crunch_points = [],
    primary_crunch_alert,
    probabilistic,
    backtest,
    assumptions = {},
    disclaimer
  } = forecast || {};

  const probDistribution = probabilistic?.daily_distribution || [];
  const riskMetrics = probabilistic?.risk_metrics || {};

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white">30-Day Cash-Flow Prediction</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Predictive liquidity projection combining scheduled obligations, expected salary, and discretionary burn rate
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setViewMode('PROBABILISTIC')}
              className={`px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition ${
                viewMode === 'PROBABILISTIC' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Monte Carlo (p10/p50/p90)
            </button>
            <button
              onClick={() => setViewMode('DETERMINISTIC')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                viewMode === 'DETERMINISTIC' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' : 'text-slate-400 hover:text-white'
              }`}
            >
              Single-Line Baseline
            </button>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            {[14, 30, 60].map(d => (
              <button
                key={d}
                onClick={() => setHorizonDays(d)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                  horizonDays === d ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {d}D
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Financial Health Score & Distress Signals Component */}
      <HealthScoreCard />

      {/* Primary Crunch Alert Banner */}
      {primary_crunch_alert && (
        <div className={`p-5 rounded-2xl border flex items-start gap-4 shadow-lg ${
          primary_crunch_alert.severity === 'CRITICAL'
            ? 'bg-rose-500/10 border-rose-500/40 text-rose-300'
            : 'bg-amber-500/10 border-amber-500/40 text-amber-300'
        }`}>
          <div className="p-3 bg-slate-900/80 rounded-xl mt-0.5">
            <AlertOctagon className={`w-7 h-7 ${
              primary_crunch_alert.severity === 'CRITICAL' ? 'text-rose-400' : 'text-amber-400'
            }`} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Impending Liquidity Crunch Detected</h3>
              <span className={`px-2 py-0.2 text-[10px] font-bold rounded-full uppercase ${
                primary_crunch_alert.severity === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}>
                {primary_crunch_alert.severity} RISK
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-medium">
              {primary_crunch_alert.message}
            </p>
            <p className="text-[11px] text-slate-400">
              💡 <strong>Preventative Action:</strong> Delay non-urgent discretionary purchases or temporarily transfer buffer funds to maintain liquidity before scheduled deductions.
            </p>
          </div>
        </div>
      )}

      {/* Probabilistic Risk Metrics Panel */}
      {viewMode === 'PROBABILISTIC' && probabilistic?.has_data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Pre-Payday Shortage Risk Card */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Pre-Payday Shortage Risk</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                riskMetrics.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                riskMetrics.risk_level === 'ELEVATED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}>
                {riskMetrics.risk_level || 'EVALUATED'}
              </span>
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-extrabold text-white font-mono">
                {riskMetrics.p_negative_pre_payday || 0}%
              </span>
              <span className="text-xs text-slate-400">P(Balance &lt; ₹0)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Risk of depleting liquid funds before next payday ({riskMetrics.first_payday_estimated || 'estimated'}). 
              P(Dipping below ₹3k buffer) is <strong>{riskMetrics.p_safety_floor_breach_pre_payday || 0}%</strong>.
            </p>
          </div>

          {/* Likely Danger Date */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Imminent Danger Date</span>
              <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400">
                <AlertOctagon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-1">
              <span className="text-2xl font-bold text-white font-mono">
                {riskMetrics.danger_date || "No Imminent Dip"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {riskMetrics.danger_date
                ? "Monte Carlo cluster where simulated debits concentrate before incoming salary credits."
                : "Liquidity trajectory remains comfortably above safety buffer across simulation horizon."}
            </p>
          </div>

          {/* Walk-Forward Backtest Card */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-indigo-400" />
                Walk-Forward Backtest
              </span>
              {backtest?.is_supported && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {backtest.coverage_quality} FIT
                </span>
              )}
            </div>

            {backtest?.is_supported ? (
              <div>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-white font-mono">
                    {backtest.empirical_coverage_pct}%
                  </span>
                  <span className="text-xs text-slate-400">80% Interval Coverage</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Actual holdout balances inside [p10, p90] interval. Mean Absolute Error: <strong>₹{backtest.mean_absolute_error?.toLocaleString('en-IN')}</strong>.
                </p>
              </div>
            ) : (
              <div className="mt-2">
                <span className="text-xs text-amber-400 font-semibold block">Insufficient History</span>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  {backtest?.reason || "Requires minimum 60 days of historical transactions to hold out 30 days."}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Current Starting Balance</span>
          <span className="text-2xl font-bold text-white mt-1 block font-mono">
            {formatINR(starting_balance)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">Verified ledger baseline</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Projected 30-Day Ending</span>
          <span className={`text-2xl font-bold mt-1 block font-mono ${
            ending_projected_balance >= 0 ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            {formatINR(ending_projected_balance)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">Simulated terminal balance</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Projected Inflows</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block font-mono">
            +{formatINR(total_projected_inflow)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">Expected salary & credits</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Projected Outflows</span>
          <span className="text-2xl font-bold text-rose-400 mt-1 block font-mono">
            -{formatINR(total_projected_outflow)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">EMIs, rent, bills & daily burn</span>
        </div>
      </div>

      {/* 30-Day Liquidity Area Chart */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              {viewMode === 'PROBABILISTIC'
                ? "Monte Carlo Probabilistic Payday Projection (2,000 Paths)"
                : "Deterministic Daily Balance Trajectory"}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {viewMode === 'PROBABILISTIC'
                ? "Showing 80% confidence interval [p10, p90] with median p50 path, bootstrapped by weekday and recurring jitter"
                : "Simulated day-by-day balance including scheduled recurring debits, salary credits, and estimated discretionary burn"}
            </p>
          </div>

          <button
            onClick={() => setWhyModal({
              open: true,
              title: viewMode === 'PROBABILISTIC' ? 'Probabilistic Monte Carlo Methodology' : 'Deterministic Projection Methodology',
              content: viewMode === 'PROBABILISTIC'
                ? (probabilistic?.methodology || 'Simulates 2,000 paths bootstrapping discretionary expenses by day-of-week and applying +/-2 day jitter to recurring payment dates.')
                : `Calculates daily ending balances starting from ${formatINR(starting_balance)}, deducting recurring obligations and average daily discretionary burn (${formatINR(assumptions.daily_discretionary_burn)}/day).`
            })}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            Methodology & Assumptions
          </button>
        </div>

        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            {viewMode === 'PROBABILISTIC' && probDistribution.length > 0 ? (
              <AreaChart data={probDistribution} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="p50Grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="fanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${v/1000}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  formatter={(val, name) => [formatINR(val), name]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <ReferenceLine y={3000} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "Safety Floor (₹3,000)", fill: "#f59e0b", fontSize: 10, position: "insideBottomRight" }} />
                <ReferenceLine y={0} stroke="#ef4444" strokeWidth={1.5} label={{ value: "Zero (Shortage)", fill: "#ef4444", fontSize: 10, position: "insideTopRight" }} />
                
                {/* p90 Upper optimistic band */}
                <Area
                  type="monotone"
                  dataKey="p90"
                  name="Optimistic (p90)"
                  stroke="#a5b4fc"
                  strokeDasharray="2 2"
                  strokeWidth={1.5}
                  fillOpacity={1}
                  fill="url(#fanGrad)"
                />

                {/* p50 Median trajectory */}
                <Area
                  type="monotone"
                  dataKey="p50"
                  name="Median Path (p50)"
                  stroke="#6366f1"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#p50Grad)"
                />

                {/* p10 Conservative lower envelope */}
                <Area
                  type="monotone"
                  dataKey="p10"
                  name="Conservative Floor (p10)"
                  stroke="#f43f5e"
                  strokeWidth={1.5}
                  fillOpacity={0}
                />
              </AreaChart>
            ) : (
              <AreaChart data={daily_projection} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="balanceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${v/1000}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  formatter={(val, name) => [formatINR(val), "Projected Balance"]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <ReferenceLine y={3000} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "Safety Floor (₹3,000)", fill: "#f87171", fontSize: 10, position: "insideBottomRight" }} />
                <ReferenceLine y={0} stroke="#dc2626" strokeWidth={1.5} />
                <Area
                  type="monotone"
                  dataKey="projected_balance"
                  name="Projected Balance"
                  stroke="#6366f1"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#balanceGrad)"
                />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Assumptions & Milestone Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulation Assumptions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-400" />
            Simulation Parameters & Assumptions
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400">Baseline Balance:</span>
              <span className="font-mono text-white font-semibold">{formatINR(starting_balance)}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400">Daily Discretionary Burn:</span>
              <span className="font-mono text-white font-semibold">
                {formatINR(assumptions.daily_discretionary_burn)}/day
              </span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400">Scheduled Obligations:</span>
              <span className="font-mono text-white font-semibold">
                {assumptions.scheduled_obligations_count || 0} event(s)
              </span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400">Expected Income Credits:</span>
              <span className="font-mono text-white font-semibold">
                {assumptions.expected_income_count || 0} payment(s)
              </span>
            </div>
          </div>

          <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-xl text-[11px] text-slate-400 leading-relaxed">
            ⚠️ <strong>Disclaimer:</strong> {disclaimer}
          </div>
        </div>

        {/* Milestone Events Timeline */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-400" />
            Projected Cash-Flow Milestones ({daily_projection.filter(d => d.events.length > 1 || d.inflow > 0).length})
          </h3>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {daily_projection.filter(d => d.events.length > 1 || d.inflow > 0).map((day) => (
              <div
                key={day.date}
                className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
                  day.is_below_safety
                    ? 'bg-amber-500/5 border-amber-500/30'
                    : 'bg-slate-800/40 border-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-300 font-semibold">{day.date}</span>
                    <span className="text-[10px] text-slate-500 font-mono">(Day {day.day_number})</span>
                    {day.is_below_safety && (
                      <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 font-bold">
                        Low Buffer
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {day.events.filter(e => !e.includes("Estimated Discretionary")).join(" • ") || "Normal discretionary burn"}
                  </div>
                </div>

                <div className="text-right font-mono">
                  <span className={`font-bold block ${day.projected_balance >= 0 ? 'text-white' : 'text-rose-400'}`}>
                    {formatINR(day.projected_balance)}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Net: {day.inflow > 0 ? `+${formatINR(day.inflow)} ` : ''}-{formatINR(day.outflow)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

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
            <p className="text-xs text-slate-300 leading-relaxed">{whyModal.content}</p>
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

