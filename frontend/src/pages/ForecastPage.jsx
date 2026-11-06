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
  Info
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
    assumptions = {},
    disclaimer
  } = forecast || {};

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

        {/* Horizon Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
          {[14, 30, 60].map(d => (
            <button
              key={d}
              onClick={() => setHorizonDays(d)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                horizonDays === d ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {d} Days
            </button>
          ))}
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
            <h3 className="text-base font-bold text-white">Daily Projected Balance Trajectory</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulated day-by-day balance including scheduled recurring debits, salary credits, and estimated discretionary burn
            </p>
          </div>

          <button
            onClick={() => setWhyModal({
              open: true,
              title: 'Cash-Flow Prediction Methodology',
              content: `This projection calculates daily ending balances by taking your current balance (${formatINR(starting_balance)}), adding expected salary credits on historical paydays, deducting recurring scheduled obligations (EMIs, rent, subscriptions), and applying your trailing 60-day average daily discretionary spending rate (${formatINR(assumptions.daily_discretionary_burn)}/day).`
            })}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            Why am I seeing this?
          </button>
        </div>

        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
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
                stroke="#6366f1"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#balanceGrad)"
              />
            </AreaChart>
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

