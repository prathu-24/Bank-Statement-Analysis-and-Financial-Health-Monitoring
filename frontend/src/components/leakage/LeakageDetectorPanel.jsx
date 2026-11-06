import React, { useState, useEffect } from 'react';
import {
  TrendingDown,
  AlertOctagon,
  Flame,
  Copy,
  Receipt,
  HelpCircle,
  ShieldAlert,
  ArrowUpRight,
  Sparkles,
  Info
} from 'lucide-react';
import { statementApi } from '../../services/api';

export default function LeakageDetectorPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [whyModalOpen, setWhyModalOpen] = useState(false);

  useEffect(() => {
    fetchLeakage();
  }, []);

  const fetchLeakage = async () => {
    try {
      const res = await statementApi.getLeakage();
      setData(res);
    } catch (err) {
      console.error("Failed to load leakage analysis:", err);
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

  if (loading || !data || !data.has_data) {
    return null;
  }

  const {
    total_annual_leakage = 0,
    annual_savings_summary = {},
    zombie_subscriptions = [],
    price_creeps = [],
    duplicate_debits = [],
    bank_charges = [],
    methodology
  } = data;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30">
              <Flame className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-white">
              Financial Leakage & Cost Creep Radar
            </h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 uppercase">
              {data.leakage_count} Inefficiencies Found
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Detects zombie subscriptions, stealth price creep, 48-hr duplicate debits, and avoidable bank penalty fees.
          </p>
        </div>

        <div className="bg-rose-500/10 border border-rose-500/25 rounded-2xl px-4 py-2.5 text-right">
          <span className="text-[10px] text-rose-400 uppercase font-bold block">
            Annualized Recoverable Waste
          </span>
          <span className="text-xl font-bold text-rose-300 font-mono">
            {formatINR(total_annual_leakage)}
          </span>
          <span className="text-[10px] text-slate-400 block">
            Est. yearly rupee leakage
          </span>
        </div>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-2xl">
          <span className="text-[10px] text-slate-400 uppercase font-semibold block">Zombie Subs</span>
          <span className="text-base font-bold text-white font-mono mt-1 block">
            {formatINR(annual_savings_summary.zombie_subscriptions_annual || 0)}/yr
          </span>
          <span className="text-[10px] text-slate-500">{zombie_subscriptions.length} active service(s)</span>
        </div>

        <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-2xl">
          <span className="text-[10px] text-slate-400 uppercase font-semibold block">Price Creep</span>
          <span className="text-base font-bold text-amber-300 font-mono mt-1 block">
            +{formatINR(annual_savings_summary.price_creep_annual || 0)}/yr
          </span>
          <span className="text-[10px] text-slate-500">{price_creeps.length} stealth price hike(s)</span>
        </div>

        <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-2xl">
          <span className="text-[10px] text-slate-400 uppercase font-semibold block">Bank & AMC Fees</span>
          <span className="text-base font-bold text-rose-300 font-mono mt-1 block">
            {formatINR(annual_savings_summary.bank_charges_annual || 0)}/yr
          </span>
          <span className="text-[10px] text-slate-500">{bank_charges.length} fee transaction(s)</span>
        </div>

        <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-2xl">
          <span className="text-[10px] text-slate-400 uppercase font-semibold block">Duplicate Debits</span>
          <span className="text-base font-bold text-emerald-300 font-mono mt-1 block">
            {formatINR(annual_savings_summary.duplicate_refunds_immediate || 0)}
          </span>
          <span className="text-[10px] text-slate-500">{duplicate_debits.length} dispute refund(s)</span>
        </div>
      </div>

      {/* Grid of Specific Leakage Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Price Creeps */}
        {price_creeps.length > 0 && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                <ArrowUpRight className="w-4 h-4" />
                Stealth Price Creep Detected
              </span>
              <span className="text-[10px] text-slate-500">Unannounced rate hikes</span>
            </div>
            <div className="space-y-2">
              {price_creeps.map((c, i) => (
                <div key={i} className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{c.merchant}</span>
                    <span className="text-amber-400 font-mono font-bold">
                      {formatINR(c.previous_amount)} &rarr; {formatINR(c.new_amount)} (+{c.percentage_increase}%)
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{c.explanation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Zombie Subscriptions */}
        {zombie_subscriptions.length > 0 && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-400 flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4" />
                Zombie Subscriptions
              </span>
              <span className="text-[10px] text-slate-500">Recurring auto-debits</span>
            </div>
            <div className="space-y-2">
              {zombie_subscriptions.map((z, i) => (
                <div key={i} className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{z.merchant}</span>
                    <span className="font-mono text-white font-bold">{formatINR(z.monthly_cost)}/mo</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Last billed: {z.last_billed}</span>
                    <span className="text-emerald-400 font-medium">{z.action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bank Charges */}
        {bank_charges.length > 0 && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5">
                <Receipt className="w-4 h-4" />
                Avoidable Bank Charges & Penalties
              </span>
              <span className="text-[10px] text-slate-500">{bank_charges.length} fee(s)</span>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {bank_charges.slice(0, 5).map((b, i) => (
                <div key={i} className="p-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-slate-300 font-medium block truncate max-w-[220px]">{b.description}</span>
                    <span className="text-[10px] text-slate-500">{b.date} &bull; {b.fee_type}</span>
                  </div>
                  <span className="font-mono text-rose-400 font-bold">{formatINR(b.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Duplicate Debits */}
        {duplicate_debits.length > 0 && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                <Copy className="w-4 h-4" />
                Rapid Duplicate Debits
              </span>
              <span className="text-[10px] text-slate-500">Same merchant & amount within 48h</span>
            </div>
            <div className="space-y-2">
              {duplicate_debits.map((d, i) => (
                <div key={i} className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{d.merchant}</span>
                    <span className="font-mono text-cyan-400 font-bold">{formatINR(d.amount)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>{d.original_date} vs {d.duplicate_date} ({d.hours_apart}h apart)</span>
                    <span className="text-rose-400 font-medium">{d.action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Methodology Note */}
      <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl flex items-center justify-between text-[11px] text-slate-400">
        <span>{methodology}</span>
        <button
          onClick={() => setWhyModalOpen(!whyModalOpen)}
          className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 flex-shrink-0 ml-3"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          Assumptions
        </button>
      </div>

      {whyModalOpen && (
        <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl text-xs text-indigo-300 space-y-1">
          <strong>Leakage Calculation Assumptions:</strong>
          <p>
            Annualization factor is 12x monthly recurrence. Price creep triggers when successive debits at the same merchant increase by &ge; 5% with &ge; ₹20 absolute increase. Duplicate detection isolates identical debits cleared within 48 hours.
          </p>
        </div>
      )}
    </div>
  );
}

